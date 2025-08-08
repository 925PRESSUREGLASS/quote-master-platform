"""
Enhanced AI Service Implementation for Quote Master Pro
Integrates OpenTelemetry tracing, circuit breakers, and smart routing.
"""

import asyncio
import hashlib
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import anthropic
import openai
import redis.asyncio as redis
import structlog
from anthropic import AsyncAnthropic
from openai import AsyncAzureOpenAI, AsyncOpenAI
from redis.exceptions import ConnectionError, ResponseError, TimeoutError

from src.core.config import get_settings
from src.core.exceptions import AIServiceError, RateLimitError

from .monitoring.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerOpenException,
    circuit_breaker_manager,
    with_circuit_breaker,
    with_intelligent_retry,
)
from .monitoring.smart_routing import (
    AIProviderRouter,
    NoProvidersAvailableException,
    ProviderConfig,
    RoutingStrategy,
    with_smart_routing,
)

# Enhanced monitoring imports
from .monitoring.tracing import (
    add_trace_attributes,
    get_meter,
    get_tracer,
    record_exception,
    trace_ai_operation,
    trace_ai_request,
)

# Configure structured logging
logger = structlog.get_logger(__name__)
settings = get_settings()


class AIProvider(Enum):
    """Enumeration of supported AI providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class ServiceCategory(Enum):
    """Enumeration of service categories for quote generation."""

    WINDOW_CLEANING = "window_cleaning"
    PRESSURE_WASHING = "pressure_washing"
    GUTTER_CLEANING = "gutter_cleaning"
    SOLAR_PANEL_CLEANING = "solar_panel_cleaning"
    ROOF_CLEANING = "roof_cleaning"
    DRIVEWAY_CLEANING = "driveway_cleaning"
    BUILDING_WASH = "building_wash"
    GRAFFITI_REMOVAL = "graffiti_removal"


@dataclass
class AIRequest:
    """Data class for AI service requests."""

    prompt: str
    context: Optional[str] = None
    category: Optional[ServiceCategory] = None
    tone: Optional[str] = "professional"
    max_tokens: int = 500
    temperature: float = 0.7
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    preferred_provider: Optional[str] = None
    routing_strategy: Optional[RoutingStrategy] = None


@dataclass
class AIResponse:
    """Enhanced data class for AI service responses."""

    text: str
    provider: AIProvider
    model: str
    tokens_used: int
    cost: float
    quality_score: float
    response_time: float
    timestamp: datetime
    request_id: str
    cached: bool = False
    routing_metadata: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        data = asdict(self)
        data["provider"] = self.provider.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


class EnhancedAIService:
    """Enhanced AI Service with comprehensive monitoring and resilience."""

    def __init__(self):
        """Initialize the enhanced AI service."""

        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None
        self.azure_client = None
        self.redis_client = None

        # Initialize monitoring infrastructure
        self._setup_monitoring()

        # Cache for responses
        self.cache_enabled = settings.enable_caching
        self.cache_ttl = settings.cache_ttl or 3600
        self._redis_available = False

        # Metrics tracking
        self.metrics = get_meter()
        self._setup_metrics()

        logger.info("Enhanced AI Service initialized with comprehensive monitoring")

    def _setup_monitoring(self):
        """Setup monitoring infrastructure."""

        # Configure provider routing
        providers = [
            ProviderConfig(
                name="openai",
                priority=1,
                weight=1.0,
                cost_per_1k_tokens=0.002,
                max_requests_per_minute=100,
                enabled=bool(settings.openai_api_key),
            ),
            ProviderConfig(
                name="anthropic",
                priority=2,
                weight=0.8,
                cost_per_1k_tokens=0.008,
                max_requests_per_minute=50,
                enabled=bool(settings.anthropic_api_key),
            ),
            ProviderConfig(
                name="azure_openai",
                priority=3,
                weight=0.9,
                cost_per_1k_tokens=0.002,
                max_requests_per_minute=80,
                enabled=bool(settings.azure_openai_api_key),
            ),
        ]

        self.router = AIProviderRouter(providers)

        # Configure circuit breakers with custom settings
        openai_config = CircuitBreakerConfig(
            failure_threshold=3, recovery_timeout=30, success_threshold=2
        )

        anthropic_config = CircuitBreakerConfig(
            failure_threshold=5, recovery_timeout=60, success_threshold=3
        )

        # Register circuit breakers
        circuit_breaker_manager.get_circuit_breaker("openai", openai_config)
        circuit_breaker_manager.get_circuit_breaker("anthropic", anthropic_config)
        circuit_breaker_manager.get_circuit_breaker("azure_openai", openai_config)

    def _setup_metrics(self):
        """Setup OpenTelemetry metrics."""

        # Request counters
        self.request_counter = self.metrics.create_counter(
            name="ai_requests_total",
            description="Total AI requests processed",
            unit="1",
        )

        self.success_counter = self.metrics.create_counter(
            name="ai_requests_successful",
            description="Successful AI requests",
            unit="1",
        )

        self.error_counter = self.metrics.create_counter(
            name="ai_requests_failed", description="Failed AI requests", unit="1"
        )

        # Response time histogram
        self.response_time_histogram = self.metrics.create_histogram(
            name="ai_response_time", description="AI request response times", unit="s"
        )

        # Token usage gauge
        self.token_usage_counter = self.metrics.create_counter(
            name="ai_tokens_used", description="Total tokens consumed", unit="1"
        )

        # Cost tracking
        self.cost_counter = self.metrics.create_counter(
            name="ai_cost_total", description="Total cost of AI requests", unit="USD"
        )

    def _init_redis_with_fallback(self):
        """Initialize Redis connection with graceful fallback."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self._redis_available = True
            logger.info("Redis cache initialized for AI service")
        except Exception as e:
            logger.warning(f"Redis unavailable for AI service, caching disabled: {e}")
            self.redis_client = None
            self._redis_available = False

    def _check_redis_health(self) -> bool:
        """Check if Redis is available and working."""
        if not self.redis_client or not self._redis_available:
            return False
        return True

    async def _async_check_redis_health(self) -> bool:
        """Async check if Redis is available and working."""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            if not self._redis_available:
                logger.info("Redis connection restored for AI service")
                self._redis_available = True
            return True
        except (ConnectionError, TimeoutError, ResponseError):
            if self._redis_available:
                logger.warning("Redis connection lost for AI service, caching disabled")
                self._redis_available = False
            return False

    async def initialize(self):
        """Initialize all AI service connections and resources."""

        with trace_ai_operation("service_initialization", "ai_service", "init"):
            try:
                # Initialize Redis cache with fallback
                if self.cache_enabled:
                    self._init_redis_with_fallback()

                # Initialize OpenAI client
                if settings.openai_api_key:
                    self.openai_client = AsyncOpenAI(
                        api_key=settings.openai_api_key, timeout=30.0
                    )
                    logger.info("OpenAI client initialized")

                # Initialize Anthropic client
                if settings.anthropic_api_key:
                    self.anthropic_client = AsyncAnthropic(
                        api_key=settings.anthropic_api_key, timeout=30.0
                    )
                    logger.info("Anthropic client initialized")

                # Initialize Azure OpenAI client
                if settings.azure_openai_api_key:
                    self.azure_client = AsyncAzureOpenAI(
                        api_key=settings.azure_openai_api_key,
                        api_version=settings.azure_openai_api_version,
                        azure_endpoint=settings.azure_openai_endpoint,
                        timeout=30.0,
                    )
                    logger.info("Azure OpenAI client initialized")

                add_trace_attributes(
                    openai_enabled=bool(self.openai_client),
                    anthropic_enabled=bool(self.anthropic_client),
                    azure_enabled=bool(self.azure_client),
                    cache_enabled=self.cache_enabled,
                    redis_available=bool(self.redis_client),
                )

            except Exception as e:
                logger.error("Failed to initialize AI service", error=str(e))
                record_exception(e)
                raise AIServiceError(f"Failed to initialize AI service: {e}")

    @trace_ai_request
    async def generate_quote(self, request: AIRequest) -> AIResponse:
        """Generate a quote using the enhanced AI service with full monitoring."""

        request_id = hashlib.md5(
            f"{request.prompt}{request.context}{time.time()}".encode()
        ).hexdigest()

        with trace_ai_operation(
            "quote_generation",
            "ai_service",
            "generation",
            {
                "request.category": request.category.value
                if request.category
                else None,
                "request.tone": request.tone,
                "request.max_tokens": request.max_tokens,
                "request.user_id": request.user_id,
                "request.session_id": request.session_id,
                "request.id": request_id,
            },
        ) as span:
            start_time = time.time()

            try:
                # Record request metrics
                self.request_counter.add(
                    1,
                    {
                        "category": request.category.value
                        if request.category
                        else "unknown",
                        "provider": "pending",
                    },
                )

                # Check cache first
                if self.cache_enabled:
                    cached_response = await self._get_cached_response(request)
                    if cached_response:
                        span.set_attribute("cache.hit", True)
                        return cached_response

                span.set_attribute("cache.hit", False)

                # Select optimal provider using smart routing
                provider_name = await self.router.select_provider(
                    request_tokens=request.max_tokens,
                    preferred_provider=request.preferred_provider,
                    strategy=request.routing_strategy,
                )

                span.set_attribute("routing.selected_provider", provider_name)
                add_trace_attributes(selected_provider=provider_name)

                # Generate response with circuit breaker protection
                response = await self._generate_with_provider(
                    provider_name, request, request_id, start_time
                )

                # Cache successful response
                if self.cache_enabled and response.quality_score > 0.7:
                    await self._cache_response(request, response)

                # Record success metrics
                self.success_counter.add(1, {"provider": provider_name})
                self.response_time_histogram.record(
                    response.response_time, {"provider": provider_name}
                )
                self.token_usage_counter.add(
                    response.tokens_used, {"provider": provider_name}
                )
                self.cost_counter.add(response.cost, {"provider": provider_name})

                return response

            except (CircuitBreakerOpenException, NoProvidersAvailableException) as e:
                # Handle infrastructure failures
                span.set_attribute("error.type", "infrastructure_failure")
                self.error_counter.add(1, {"error_type": "infrastructure"})
                record_exception(e)

                # Try fallback strategy
                fallback_response = await self._handle_infrastructure_failure(
                    request, request_id, start_time
                )
                if fallback_response:
                    return fallback_response

                raise AIServiceError(f"All AI providers unavailable: {e}")

            except Exception as e:
                # Handle general errors
                span.set_attribute("error.type", "general_error")
                self.error_counter.add(1, {"error_type": "general"})
                record_exception(e)

                logger.error(
                    "Quote generation failed", request_id=request_id, error=str(e)
                )
                raise AIServiceError(f"Failed to generate quote: {e}")

    async def _generate_with_provider(
        self, provider_name: str, request: AIRequest, request_id: str, start_time: float
    ) -> AIResponse:
        """Generate response with specific provider using circuit breaker."""

        # Apply circuit breaker protection
        circuit_breaker = circuit_breaker_manager.get_circuit_breaker(provider_name)

        async def provider_call():
            if provider_name == "openai":
                return await self._call_openai(request, request_id)
            elif provider_name == "anthropic":
                return await self._call_anthropic(request, request_id)
            elif provider_name == "azure_openai":
                return await self._call_azure_openai(request, request_id)
            else:
                raise ValueError(f"Unknown provider: {provider_name}")

        # Execute with circuit breaker and retry logic
        response = await circuit_breaker.call(provider_call)

        # Update router metrics
        response_time = time.time() - start_time
        await self.router.record_request_success(
            provider_name, response_time, response.tokens_used, response.cost
        )

        return response

    @with_intelligent_retry(max_attempts=3)
    async def _call_openai(self, request: AIRequest, request_id: str) -> AIResponse:
        """Call OpenAI API with comprehensive error handling."""

        if not self.openai_client:
            raise AIServiceError("OpenAI client not initialized")

        try:
            messages = self._build_openai_messages(request)

            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout=30.0,
            )

            return AIResponse(
                text=response.choices[0].message.content,
                provider=AIProvider.OPENAI,
                model=settings.openai_model,
                tokens_used=response.usage.total_tokens,
                cost=self._calculate_cost(response.usage.total_tokens, "openai"),
                quality_score=self._score_response_quality(
                    response.choices[0].message.content, request
                ),
                response_time=0.0,  # Set by caller
                timestamp=datetime.now(),
                request_id=request_id,
                routing_metadata={
                    "provider_latency": response.usage.total_tokens
                    / 1000  # Rough estimate
                },
            )

        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise AIServiceError(f"OpenAI request failed: {e}")

    @with_intelligent_retry(max_attempts=3)
    async def _call_anthropic(self, request: AIRequest, request_id: str) -> AIResponse:
        """Call Anthropic API with comprehensive error handling."""

        if not self.anthropic_client:
            raise AIServiceError("Anthropic client not initialized")

        try:
            # Use the Messages API (new format)
            messages = [
                {"role": "user", "content": self._build_anthropic_prompt(request)}
            ]

            response = await self.anthropic_client.messages.create(
                model=settings.anthropic_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout=30.0,
            )

            # Extract text content
            response_text = ""
            if response.content and len(response.content) > 0:
                if hasattr(response.content[0], "text"):
                    response_text = response.content[0].text
                else:
                    response_text = str(response.content[0])

            # Estimate token usage (Anthropic provides usage info in newer versions)
            tokens_used = getattr(response, "usage", {}).get("output_tokens", 0)
            if tokens_used == 0:
                # Fallback estimation
                tokens_used = len(response_text.split()) + len(request.prompt.split())

            return AIResponse(
                text=response_text,
                provider=AIProvider.ANTHROPIC,
                model=settings.anthropic_model,
                tokens_used=tokens_used,
                cost=self._calculate_cost(tokens_used, "anthropic"),
                quality_score=self._score_response_quality(response_text, request),
                response_time=0.0,  # Set by caller
                timestamp=datetime.now(),
                request_id=request_id,
            )

        except Exception as e:
            logger.error("Anthropic API call failed", error=str(e))
            raise AIServiceError(f"Anthropic request failed: {e}")

    @with_intelligent_retry(max_attempts=3)
    async def _call_azure_openai(
        self, request: AIRequest, request_id: str
    ) -> AIResponse:
        """Call Azure OpenAI API with comprehensive error handling."""

        if not self.azure_client:
            raise AIServiceError("Azure OpenAI client not initialized")

        try:
            messages = self._build_openai_messages(request)

            response = await self.azure_client.chat.completions.create(
                model=settings.azure_openai_deployment_name,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                timeout=30.0,
            )

            return AIResponse(
                text=response.choices[0].message.content,
                provider=AIProvider.AZURE_OPENAI,
                model=settings.azure_openai_deployment_name,
                tokens_used=response.usage.total_tokens,
                cost=self._calculate_cost(response.usage.total_tokens, "azure_openai"),
                quality_score=self._score_response_quality(
                    response.choices[0].message.content, request
                ),
                response_time=0.0,  # Set by caller
                timestamp=datetime.now(),
                request_id=request_id,
            )

        except Exception as e:
            logger.error("Azure OpenAI API call failed", error=str(e))
            raise AIServiceError(f"Azure OpenAI request failed: {e}")

    def _build_openai_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """Build OpenAI chat messages from request."""

        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt(request.category, request.tone),
            }
        ]

        if request.context:
            messages.append({"role": "user", "content": f"Context: {request.context}"})

        messages.append({"role": "user", "content": request.prompt})

        return messages

    def _build_anthropic_prompt(self, request: AIRequest) -> str:
        """Build Anthropic prompt from request."""

        system_prompt = self._get_system_prompt(request.category, request.tone)

        prompt_parts = [f"Human: {system_prompt}\n"]

        if request.context:
            prompt_parts.append(f"Context: {request.context}\n")

        prompt_parts.extend([f"Request: {request.prompt}\n", "Assistant:"])

        return "\n".join(prompt_parts)

    def _get_system_prompt(self, category: Optional[ServiceCategory], tone: str) -> str:
        """Get system prompt based on service category and tone."""

        base_prompt = (
            f"You are a professional service quote generator with a {tone} tone. "
            "Generate accurate, detailed quotes based on the provided information. "
        )

        if category:
            category_prompts = {
                ServiceCategory.WINDOW_CLEANING: "Focus on window cleaning services, including interior/exterior cleaning, frequency options, and safety considerations.",
                ServiceCategory.PRESSURE_WASHING: "Focus on pressure washing services for various surfaces, equipment specifications, and appropriate pressure levels.",
                ServiceCategory.GUTTER_CLEANING: "Focus on gutter cleaning and maintenance services, including debris removal and downspout clearing.",
                # Add more category-specific prompts as needed
            }

            base_prompt += category_prompts.get(
                category, "Focus on general cleaning and maintenance services."
            )

        return base_prompt

    def _calculate_cost(self, tokens: int, provider: str) -> float:
        """Calculate cost based on token usage and provider rates."""

        rates = {
            "openai": 0.002,  # Per 1K tokens
            "anthropic": 0.008,  # Per 1K tokens
            "azure_openai": 0.002,  # Per 1K tokens
        }

        rate = rates.get(provider, 0.002)
        return (tokens / 1000) * rate

    def _score_response_quality(self, response_text: str, request: AIRequest) -> float:
        """Score the quality of generated response."""

        # Simple quality scoring based on various factors
        score = 1.0

        # Length check
        if len(response_text) < 50:
            score *= 0.5
        elif len(response_text) > 2000:
            score *= 0.8

        # Check for common issues
        if "I cannot" in response_text or "I don't have" in response_text:
            score *= 0.3

        # Category-specific scoring could be added here

        return max(0.0, min(1.0, score))

    async def _get_cached_response(self, request: AIRequest) -> Optional[AIResponse]:
        """Get cached response if available."""

        if not await self._async_check_redis_health():
            return None

        try:
            cache_key = self._generate_cache_key(request)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                response_data = json.loads(cached_data)
                response_data["cached"] = True
                response_data["provider"] = AIProvider(response_data["provider"])
                response_data["timestamp"] = datetime.fromisoformat(
                    response_data["timestamp"]
                )

                return AIResponse(**response_data)

        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.warning("Cache retrieval failed in AI service", error=str(e))
            self._redis_available = False

        return None

    async def _cache_response(self, request: AIRequest, response: AIResponse) -> None:
        """Cache response for future use."""

        if not await self._async_check_redis_health():
            return

        try:
            cache_key = self._generate_cache_key(request)
            cache_data = response.to_dict()
            cache_data["cached"] = False  # Mark as original when caching

            await self.redis_client.setex(
                cache_key, self.cache_ttl, json.dumps(cache_data)
            )

        except (ConnectionError, TimeoutError, ResponseError) as e:
            logger.warning("Cache storage failed in AI service", error=str(e))
            self._redis_available = False

    def _generate_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request."""

        key_components = [
            request.prompt,
            request.context or "",
            request.category.value if request.category else "",
            request.tone,
            str(request.max_tokens),
            str(request.temperature),
        ]

        key_string = "|".join(key_components)
        return f"ai_response:{hashlib.sha256(key_string.encode()).hexdigest()}"

    async def _handle_infrastructure_failure(
        self, request: AIRequest, request_id: str, start_time: float
    ) -> Optional[AIResponse]:
        """Handle infrastructure failures with fallback strategies."""

        # Could implement fallback strategies like:
        # 1. Template-based responses
        # 2. Cached similar responses
        # 3. Simplified local generation

        logger.warning("All AI providers failed, implementing fallback strategy")

        # For now, return None to indicate failure
        # In production, you might want to return a template response
        return None

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of AI service."""

        return {
            "service_status": "healthy",
            "providers": self.router.get_provider_stats(),
            "circuit_breakers": circuit_breaker_manager.get_all_health_status(),
            "cache_enabled": self.cache_enabled,
            "redis_available": self._redis_available,
            "timestamp": datetime.now().isoformat(),
        }

    async def cleanup(self):
        """Cleanup resources."""

        if self.redis_client:
            try:
                await self.redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection in AI service: {e}")

        logger.info("AI Service cleanup completed")


# Global service instance
_ai_service_instance = None


async def get_ai_service() -> EnhancedAIService:
    """Get or create the global AI service instance."""

    global _ai_service_instance

    if _ai_service_instance is None:
        _ai_service_instance = EnhancedAIService()
        await _ai_service_instance.initialize()

    return _ai_service_instance
