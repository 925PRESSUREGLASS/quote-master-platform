"""
AI Service Implementation for Quote Master Pro

This module provides a comprehensive AI service that supports multiple providers
(OpenAI, Anthropic, Azure OpenAI) with automatic fallback, retry logic, rate limiting,
cost tracking, response caching, and quality scoring.

Author: Quote Master Pro Development Team
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import aiohttp
import openai
import anthropic
from openai import AsyncAzureOpenAI, AsyncOpenAI
from anthropic import AsyncAnthropic
import redis.asyncio as redis
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

from src.core.config import get_settings
from src.core.exceptions import AIServiceError, RateLimitError


# Configure logging
logger = logging.getLogger(__name__)


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


@dataclass
class AIResponse:
    """Data class for AI service responses."""
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for serialization."""
        data = asdict(self)
        # Convert enum to string for JSON serialization
        data['provider'] = self.provider.value
        # Convert datetime to ISO string
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ProviderMetrics:
    """Metrics tracking for AI providers."""
    requests_count: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    rate_limit_remaining: int = 1000
    rate_limit_reset: Optional[datetime] = None


class RateLimiter:
    """Rate limiter implementation for AI providers."""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
        self._lock = asyncio.Lock()
    
    async def can_proceed(self) -> bool:
        """Check if request can proceed based on rate limits."""
        async with self._lock:
            now = time.time()
            # Remove old requests outside the time window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            return len(self.requests) < self.max_requests
    
    async def record_request(self) -> None:
        """Record a new request timestamp."""
        async with self._lock:
            self.requests.append(time.time())


class QualityScorer:
    """Quality scoring system for generated quotes."""
    
    QUALITY_METRICS = {
        'length': {'min': 20, 'max': 200, 'weight': 0.2},
        'coherence': {'weight': 0.3},
        'relevance': {'weight': 0.25},
        'originality': {'weight': 0.15},
        'grammar': {'weight': 0.1}
    }
    
    @classmethod
    def score_quote(cls, text: str, request: AIRequest) -> float:
        """
        Calculate quality score for generated quote.
        
        Args:
            text: Generated quote text
            request: Original AI request
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not text or not text.strip():
            return 0.0
        
        scores = {}
        
        # Length score
        length = len(text.strip())
        length_metrics = cls.QUALITY_METRICS['length']
        if length < length_metrics['min']:
            scores['length'] = length / length_metrics['min']
        elif length > length_metrics['max']:
            scores['length'] = max(0.5, 1.0 - (length - length_metrics['max']) / 100)
        else:
            scores['length'] = 1.0
        
        # Basic coherence check (sentence structure)
        sentences = text.split('.')
        coherence_score = min(1.0, len([s for s in sentences if len(s.strip()) > 10]) / max(1, len(sentences)))
        scores['coherence'] = coherence_score
        
        # Relevance score (keyword matching with request)
        if request.context:
            context_words = set(request.context.lower().split())
            text_words = set(text.lower().split())
            overlap = len(context_words.intersection(text_words))
            scores['relevance'] = min(1.0, overlap / max(1, len(context_words)))
        else:
            scores['relevance'] = 0.8  # Default relevance score
        
        # Originality score (basic uniqueness check)
        unique_words = len(set(text.lower().split()))
        total_words = len(text.split())
        scores['originality'] = unique_words / max(1, total_words) if total_words > 0 else 0.0
        
        # Grammar score (basic punctuation and capitalization check)
        grammar_score = 1.0
        if not text[0].isupper():
            grammar_score -= 0.3
        if not text.rstrip().endswith(('.', '!', '?')):
            grammar_score -= 0.3
        scores['grammar'] = max(0.0, grammar_score)
        
        # Calculate weighted final score
        final_score = sum(
            scores[metric] * cls.QUALITY_METRICS[metric]['weight']
            for metric in scores
        )
        
        return round(final_score, 3)


class AIService:
    """
    Comprehensive AI service supporting multiple providers with advanced features.
    
    Features:
    - Multiple AI providers (OpenAI, Anthropic, Azure OpenAI)
    - Automatic provider fallback
    - Retry logic with exponential backoff
    - Rate limiting per provider
    - Cost tracking and monitoring
    - Response caching with Redis
    - Quality scoring for generated content
    - Comprehensive error handling and logging
    """
    
    def __init__(self):
        """Initialize the AI service with configuration and providers."""
        self.settings = get_settings()
        self._setup_logging()
        self._initialize_clients()
        self._initialize_cache()
        self._initialize_rate_limiters()
        self._initialize_metrics()
        
        # Provider priority order for fallback
        self.provider_priority = [
            AIProvider.OPENAI,
            AIProvider.ANTHROPIC,
            AIProvider.AZURE_OPENAI
        ]
        
        # Cost per token by provider (approximate values in USD)
        self.cost_per_token = {
            AIProvider.OPENAI: {
                "gpt-4": {"input": 0.00003, "output": 0.00006},
                "gpt-3.5-turbo": {"input": 0.0000015, "output": 0.000002}
            },
            AIProvider.ANTHROPIC: {
                "claude-3-opus": {"input": 0.000015, "output": 0.000075},
                "claude-3-sonnet": {"input": 0.000003, "output": 0.000015}
            },
            AIProvider.AZURE_OPENAI: {
                "gpt-4": {"input": 0.00003, "output": 0.00006},
                "gpt-35-turbo": {"input": 0.0000015, "output": 0.000002}
            }
        }
    
    def _setup_logging(self) -> None:
        """Configure logging for the AI service."""
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    def _initialize_clients(self) -> None:
        """Initialize AI provider clients."""
        self.clients = {}
        
        # OpenAI client
        if self.settings.OPENAI_API_KEY:
            self.clients[AIProvider.OPENAI] = AsyncOpenAI(
                api_key=self.settings.OPENAI_API_KEY
            )
            logger.info("OpenAI client initialized")
        
        # Anthropic client
        if self.settings.ANTHROPIC_API_KEY:
            self.clients[AIProvider.ANTHROPIC] = AsyncAnthropic(
                api_key=self.settings.ANTHROPIC_API_KEY
            )
            logger.info("Anthropic client initialized")
        
        # Azure OpenAI client
        if (self.settings.AZURE_OPENAI_API_KEY and 
            self.settings.AZURE_OPENAI_ENDPOINT):
            self.clients[AIProvider.AZURE_OPENAI] = AsyncAzureOpenAI(
                api_key=self.settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT,
                api_version="2024-02-01"
            )
            logger.info("Azure OpenAI client initialized")
        
        if not self.clients:
            raise AIServiceError("No AI providers configured")
    
    def _initialize_cache(self) -> None:
        """Initialize Redis cache connection."""
        try:
            redis_url = getattr(self.settings, 'REDIS_URL', 'redis://localhost:6379')
            self.cache = redis.from_url(redis_url, decode_responses=True)
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}")
            self.cache = None
    
    def _initialize_rate_limiters(self) -> None:
        """Initialize rate limiters for each provider."""
        self.rate_limiters = {
            AIProvider.OPENAI: RateLimiter(max_requests=60, time_window=60),
            AIProvider.ANTHROPIC: RateLimiter(max_requests=50, time_window=60),
            AIProvider.AZURE_OPENAI: RateLimiter(max_requests=60, time_window=60)
        }
    
    def _initialize_metrics(self) -> None:
        """Initialize metrics tracking for providers."""
        self.metrics = {
            provider: ProviderMetrics() for provider in AIProvider
        }
    
    def _generate_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request."""
        request_data = {
            'prompt': request.prompt,
            'context': request.context,
            'category': request.category.value if request.category else None,
            'tone': request.tone,
            'max_tokens': request.max_tokens,
            'temperature': request.temperature
        }
        request_str = json.dumps(request_data, sort_keys=True)
        return f"ai_service:{hashlib.md5(request_str.encode()).hexdigest()}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[AIResponse]:
        """Retrieve cached response if available."""
        if not self.cache:
            return None
        
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                data['cached'] = True
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                return AIResponse(**data)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    async def _cache_response(self, cache_key: str, response: AIResponse, ttl: int = 3600) -> None:
        """Cache response with specified TTL."""
        if not self.cache:
            return
        
        try:
            response_data = response.to_dict()
            response_data['timestamp'] = response.timestamp.isoformat()
            await self.cache.setex(
                cache_key, 
                ttl, 
                json.dumps(response_data)
            )
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
    
    async def _check_rate_limit(self, provider: AIProvider) -> bool:
        """Check if request can proceed based on rate limits."""
        rate_limiter = self.rate_limiters.get(provider)
        if not rate_limiter:
            return True
        
        can_proceed = await rate_limiter.can_proceed()
        if not can_proceed:
            logger.warning(f"Rate limit exceeded for provider {provider.value}")
            raise RateLimitError(f"Rate limit exceeded for {provider.value}")
        
        await rate_limiter.record_request()
        return True
    
    def _calculate_cost(self, provider: AIProvider, model: str, tokens_used: int) -> float:
        """Calculate cost for API request."""
        provider_costs = self.cost_per_token.get(provider, {})
        model_costs = provider_costs.get(model, {"input": 0.00001, "output": 0.00002})
        
        # Assume 75% input tokens, 25% output tokens (rough estimate)
        input_tokens = int(tokens_used * 0.75)
        output_tokens = int(tokens_used * 0.25)
        
        cost = (input_tokens * model_costs["input"]) + (output_tokens * model_costs["output"])
        return round(cost, 6)
    
    def _update_metrics(self, provider: AIProvider, response: Optional[AIResponse] = None, 
                       error: bool = False) -> None:
        """Update provider metrics."""
        metrics = self.metrics[provider]
        metrics.requests_count += 1
        metrics.last_request_time = datetime.now()
        
        if error:
            metrics.failed_requests += 1
        elif response:
            metrics.successful_requests += 1
            metrics.total_tokens += response.tokens_used
            metrics.total_cost += response.cost
            
            # Update average response time
            total_response_time = (metrics.average_response_time * 
                                 (metrics.successful_requests - 1) + response.response_time)
            metrics.average_response_time = total_response_time / metrics.successful_requests
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, openai.APIError, anthropic.APIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )
    async def _call_openai(self, request: AIRequest) -> AIResponse:
        """Call OpenAI API with retry logic."""
        start_time = time.time()
        client = self.clients[AIProvider.OPENAI]
        
        model = "gpt-4" if request.max_tokens > 1000 else "gpt-3.5-turbo"
        
        messages = [
            {"role": "system", "content": self._build_system_prompt(request)},
            {"role": "user", "content": request.prompt}
        ]
        
        if request.context:
            messages.insert(1, {"role": "user", "content": f"Context: {request.context}"})
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                user=request.user_id or "anonymous"
            )
            
            response_time = time.time() - start_time
            text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            cost = self._calculate_cost(AIProvider.OPENAI, model, tokens_used)
            quality_score = QualityScorer.score_quote(text, request)
            
            ai_response = AIResponse(
                text=text,
                provider=AIProvider.OPENAI,
                model=model,
                tokens_used=tokens_used,
                cost=cost,
                quality_score=quality_score,
                response_time=response_time,
                timestamp=datetime.now(),
                request_id=response.id or f"openai_{int(time.time())}"
            )
            
            self._update_metrics(AIProvider.OPENAI, ai_response)
            return ai_response
            
        except Exception as e:
            self._update_metrics(AIProvider.OPENAI, error=True)
            logger.error(f"OpenAI API error: {e}")
            raise AIServiceError(f"OpenAI request failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(anthropic.APIError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )
    async def _call_anthropic(self, request: AIRequest) -> AIResponse:
        """Call Anthropic API with retry logic."""
        start_time = time.time()
        client = self.clients[AIProvider.ANTHROPIC]
        
        model = "claude-3-sonnet-20240229"
        
        prompt = self._build_anthropic_prompt(request)
        
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_time = time.time() - start_time
            text = response.content[0].text.strip()
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self._calculate_cost(AIProvider.ANTHROPIC, model, tokens_used)
            quality_score = QualityScorer.score_quote(text, request)
            
            ai_response = AIResponse(
                text=text,
                provider=AIProvider.ANTHROPIC,
                model=model,
                tokens_used=tokens_used,
                cost=cost,
                quality_score=quality_score,
                response_time=response_time,
                timestamp=datetime.now(),
                request_id=response.id or f"anthropic_{int(time.time())}"
            )
            
            self._update_metrics(AIProvider.ANTHROPIC, ai_response)
            return ai_response
            
        except Exception as e:
            self._update_metrics(AIProvider.ANTHROPIC, error=True)
            logger.error(f"Anthropic API error: {e}")
            raise AIServiceError(f"Anthropic request failed: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(openai.APIError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )
    async def _call_azure_openai(self, request: AIRequest) -> AIResponse:
        """Call Azure OpenAI API with retry logic."""
        start_time = time.time()
        client = self.clients[AIProvider.AZURE_OPENAI]
        
        model = "gpt-4" if request.max_tokens > 1000 else "gpt-35-turbo"
        
        messages = [
            {"role": "system", "content": self._build_system_prompt(request)},
            {"role": "user", "content": request.prompt}
        ]
        
        if request.context:
            messages.insert(1, {"role": "user", "content": f"Context: {request.context}"})
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                user=request.user_id or "anonymous"
            )
            
            response_time = time.time() - start_time
            text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            cost = self._calculate_cost(AIProvider.AZURE_OPENAI, model, tokens_used)
            quality_score = QualityScorer.score_quote(text, request)
            
            ai_response = AIResponse(
                text=text,
                provider=AIProvider.AZURE_OPENAI,
                model=model,
                tokens_used=tokens_used,
                cost=cost,
                quality_score=quality_score,
                response_time=response_time,
                timestamp=datetime.now(),
                request_id=response.id or f"azure_{int(time.time())}"
            )
            
            self._update_metrics(AIProvider.AZURE_OPENAI, ai_response)
            return ai_response
            
        except Exception as e:
            self._update_metrics(AIProvider.AZURE_OPENAI, error=True)
            logger.error(f"Azure OpenAI API error: {e}")
            raise AIServiceError(f"Azure OpenAI request failed: {str(e)}")
    
    def _build_system_prompt(self, request: AIRequest) -> str:
        """Build system prompt for OpenAI-style APIs."""
        prompt = "You are an expert quote generator for a professional glass repair service."
        
        if request.category:
            prompt += f" Generate a {request.category.value} quote."
        
        if request.tone:
            prompt += f" Use a {request.tone} tone."
        
        prompt += " Ensure the quote is relevant, engaging, and appropriate for the context."
        prompt += " Keep it concise but meaningful."
        
        return prompt
    
    def _build_anthropic_prompt(self, request: AIRequest) -> str:
        """Build prompt for Anthropic API."""
        prompt = "Generate a professional quote for a glass repair service."
        
        if request.category:
            prompt += f" The quote should be {request.category.value}."
        
        if request.tone:
            prompt += f" Use a {request.tone} tone."
        
        if request.context:
            prompt += f" Context: {request.context}"
        
        prompt += f"\n\nUser request: {request.prompt}"
        prompt += "\n\nProvide only the quote without additional explanation."
        
        return prompt
    
    async def generate_quote(self, request: AIRequest, 
                           preferred_provider: Optional[AIProvider] = None,
                           use_cache: bool = True) -> AIResponse:
        """
        Generate a quote using AI service with fallback support.
        
        Args:
            request: AI request configuration
            preferred_provider: Preferred AI provider (optional)
            use_cache: Whether to use response caching
            
        Returns:
            AI response with generated quote
            
        Raises:
            AIServiceError: When all providers fail
            RateLimitError: When rate limits are exceeded
        """
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache first
        if use_cache:
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.info("Returning cached response")
                return cached_response
        
        # Determine provider order
        if preferred_provider and preferred_provider in self.clients:
            providers = [preferred_provider] + [
                p for p in self.provider_priority if p != preferred_provider and p in self.clients
            ]
        else:
            providers = [p for p in self.provider_priority if p in self.clients]
        
        last_error = None
        
        # Try each provider in order
        for provider in providers:
            try:
                # Check rate limits
                await self._check_rate_limit(provider)
                
                # Call provider
                logger.info(f"Attempting request with provider: {provider.value}")
                
                if provider == AIProvider.OPENAI:
                    response = await self._call_openai(request)
                elif provider == AIProvider.ANTHROPIC:
                    response = await self._call_anthropic(request)
                elif provider == AIProvider.AZURE_OPENAI:
                    response = await self._call_azure_openai(request)
                else:
                    continue
                
                # Cache successful response
                if use_cache:
                    await self._cache_response(cache_key, response)
                
                logger.info(f"Successful response from {provider.value}")
                return response
                
            except RateLimitError:
                # Don't retry on rate limits, move to next provider
                logger.warning(f"Rate limit exceeded for {provider.value}, trying next provider")
                continue
                
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider.value} failed: {e}")
                continue
        
        # All providers failed
        error_msg = f"All AI providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise AIServiceError(error_msg)
    
    async def generate_multiple_quotes(self, request: AIRequest, count: int = 3,
                                     preferred_provider: Optional[AIProvider] = None) -> List[AIResponse]:
        """
        Generate multiple quote variations.
        
        Args:
            request: AI request configuration
            count: Number of quotes to generate
            preferred_provider: Preferred AI provider
            
        Returns:
            List of AI responses with generated quotes
        """
        tasks = []
        for i in range(count):
            # Slightly vary temperature for different results
            varied_request = AIRequest(
                prompt=request.prompt,
                context=request.context,
                category=request.category,
                tone=request.tone,
                max_tokens=request.max_tokens,
                temperature=min(1.0, request.temperature + (i * 0.1)),
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            task = self.generate_quote(
                varied_request, 
                preferred_provider=preferred_provider,
                use_cache=False  # Don't cache variations
            )
            tasks.append(task)
        
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful responses
            successful_responses = [
                resp for resp in responses 
                if isinstance(resp, AIResponse)
            ]
            
            # Sort by quality score (highest first)
            successful_responses.sort(key=lambda r: r.quality_score, reverse=True)
            
            return successful_responses
            
        except Exception as e:
            logger.error(f"Error generating multiple quotes: {e}")
            raise AIServiceError(f"Failed to generate multiple quotes: {str(e)}")
    
    async def get_metrics(self) -> Dict[str, ProviderMetrics]:
        """Get current provider metrics."""
        return {
            provider.value: metrics 
            for provider, metrics in self.metrics.items()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all providers.
        
        Returns:
            Health status for each provider
        """
        health_status = {}
        
        for provider in self.clients:
            try:
                test_request = AIRequest(
                    prompt="Test",
                    max_tokens=10,
                    temperature=0.1
                )
                
                start_time = time.time()
                
                if provider == AIProvider.OPENAI:
                    await self._call_openai(test_request)
                elif provider == AIProvider.ANTHROPIC:
                    await self._call_anthropic(test_request)
                elif provider == AIProvider.AZURE_OPENAI:
                    await self._call_azure_openai(test_request)
                
                response_time = time.time() - start_time
                
                health_status[provider.value] = {
                    "status": "healthy",
                    "response_time": response_time,
                    "last_check": datetime.now().isoformat()
                }
                
            except Exception as e:
                health_status[provider.value] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
        
        return health_status
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.cache:
            await self.cache.close()
        
        # Close any other resources if needed
        logger.info("AI Service resources cleaned up")


# Global service instance
_ai_service: Optional[AIService] = None


async def get_ai_service() -> AIService:
    """
    Get or create AI service instance (dependency injection).
    
    Returns:
        AI service instance
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


@asynccontextmanager
async def ai_service_context():
    """Context manager for AI service lifecycle."""
    service = await get_ai_service()
    try:
        yield service
    finally:
        await service.close()


# Convenience functions for common use cases
async def generate_motivational_quote(prompt: str, context: Optional[str] = None, 
                                    user_id: Optional[str] = None) -> AIResponse:
    """Generate a motivational quote."""
    service = await get_ai_service()
    request = AIRequest(
        prompt=prompt,
        context=context,
        category=ServiceCategory.WINDOW_CLEANING,
        tone="inspiring",
        user_id=user_id
    )
    return await service.generate_quote(request)


async def generate_professional_quote(prompt: str, context: Optional[str] = None,
                                     user_id: Optional[str] = None) -> AIResponse:
    """Generate a professional service quote."""
    service = await get_ai_service()
    request = AIRequest(
        prompt=prompt,
        context=context,
        category=ServiceCategory.PRESSURE_WASHING,
        tone="professional",
        max_tokens=300,
        user_id=user_id
    )
    return await service.generate_quote(request)


async def generate_quote_variations(prompt: str, count: int = 3, 
                                   context: Optional[str] = None,
                                   user_id: Optional[str] = None) -> List[AIResponse]:
    """Generate multiple service quote variations."""
    service = await get_ai_service()
    request = AIRequest(
        prompt=prompt,
        context=context,
        category=ServiceCategory.GUTTER_CLEANING,
        user_id=user_id
    )
    return await service.generate_multiple_quotes(request, count=count)
