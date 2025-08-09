"""AI orchestrator for managing multiple AI services and intelligent routing."""

import asyncio
import logging
import random
from enum import Enum
from typing import Any, Dict, List, Optional

from src.core.config import get_settings

from .base import AIRequest, AIResponse, AIServiceBase, AIServiceError, AITaskType
from .claude import ClaudeService
from .codex import CodexService
from .openai import OpenAIService

logger = logging.getLogger(__name__)
settings = get_settings()


class RoutingStrategy(str, Enum):
    """AI routing strategies."""

    ROUND_ROBIN = "round_robin"
    PERFORMANCE_BASED = "performance_based"
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    RANDOM = "random"
    SPECIFIC_MODEL = "specific_model"


class ServiceHealth(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class AIOrchestrator:
    """Orchestrates multiple AI services for optimal performance and reliability."""

    def __init__(self):
        self.services: Dict[str, AIServiceBase] = {}
        self.service_health: Dict[str, ServiceHealth] = {}
        self.service_metrics: Dict[str, Dict[str, Any]] = {}
        self.routing_strategy = RoutingStrategy.PERFORMANCE_BASED
        self.fallback_enabled = True
        self._round_robin_index = 0

        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize all available AI services."""

        try:
            # Initialize OpenAI services with new models
            if settings.openai_api_key:
                # Add GPT-5 and o3-pro when available (placeholders for future)
                models_to_init = [
                    ("openai_gpt4o", "gpt-4o"),
                    ("openai_gpt4o_mini", "gpt-4o-mini"),
                    ("openai_gpt4_turbo", "gpt-4-turbo"),
                    ("openai_gpt35", "gpt-3.5-turbo"),
                    # Future models (will be enabled when available)
                    # ("openai_gpt5", "gpt-5"),
                    # ("openai_o3_pro", "o3-pro"),
                ]

                for service_key, model_name in models_to_init:
                    try:
                        self.services[service_key] = OpenAIService(
                            model_name=model_name
                        )
                        self.service_health[service_key] = ServiceHealth.HEALTHY
                        logger.info(f"Initialized OpenAI service: {model_name}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize {model_name}: {e}")

                logger.info(
                    f"OpenAI services initialized: {len([k for k in self.services.keys() if 'openai' in k])} models"
                )
            else:
                logger.warning("OpenAI API key not found, skipping OpenAI services")

            # Initialize Claude services
            if settings.anthropic_api_key:
                claude_models = [
                    ("claude_opus", "claude-3-opus-20240229"),
                    ("claude_sonnet", "claude-3-sonnet-20240229"),
                    ("claude_haiku", "claude-3-haiku-20240307"),
                ]

                for service_key, model_name in claude_models:
                    try:
                        self.services[service_key] = ClaudeService(
                            model_name=model_name
                        )
                        self.service_health[service_key] = ServiceHealth.HEALTHY
                        logger.info(f"Initialized Claude service: {model_name}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize {model_name}: {e}")

                logger.info(
                    f"Claude services initialized: {len([k for k in self.services.keys() if 'claude' in k])} models"
                )
            else:
                logger.warning("Anthropic API key not found, skipping Claude services")

            # Initialize Codex services for code generation
            if settings.openai_api_key:  # Codex uses same OpenAI key
                codex_models = [
                    ("codex_davinci", "code-davinci-002"),
                    ("codex_cushman", "code-cushman-001"),
                ]

                for service_key, model_name in codex_models:
                    try:
                        self.services[service_key] = CodexService(model_name=model_name)
                        self.service_health[service_key] = ServiceHealth.HEALTHY
                        logger.info(f"Initialized Codex service: {model_name}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize {model_name}: {e}")

                if any("codex" in k for k in self.services.keys()):
                    logger.info(
                        f"Codex services initialized: {len([k for k in self.services.keys() if 'codex' in k])} models"
                    )
            else:
                logger.warning("OpenAI API key not found, skipping Codex services")

            # Initialize metrics for all services
            for service_name in self.services.keys():
                self.service_metrics[service_name] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "avg_response_time": 0.0,
                    "avg_cost": 0.0,
                    "avg_quality_score": 0.0,
                    "last_used": None,
                }

            if not self.services:
                raise AIServiceError(
                    "No AI services could be initialized", "Orchestrator"
                )

            logger.info(
                f"AI Orchestrator initialized with {len(self.services)} services"
            )

        except Exception as e:
            logger.error(f"Failed to initialize AI services: {str(e)}")
            raise AIServiceError(
                f"AI Orchestrator initialization failed: {str(e)}", "Orchestrator"
            )

    async def generate_text(
        self,
        request: AIRequest,
        routing_strategy: Optional[RoutingStrategy] = None,
        preferred_service: Optional[str] = None,
    ) -> AIResponse:
        """Generate text using the best available AI service."""

        strategy = routing_strategy or self.routing_strategy

        try:
            # Select the appropriate service
            service_name = self._select_service(request, strategy, preferred_service)

            if not service_name:
                raise AIServiceError("No suitable AI service available", "Orchestrator")

            # Make the request
            service = self.services[service_name]
            response = await service.generate_text(request)

            # Update metrics
            await self._update_service_metrics(service_name, response, success=True)

            return response

        except AIServiceError as e:
            # Try fallback if enabled and original request failed
            if self.fallback_enabled and preferred_service:
                logger.warning(f"Primary service failed, trying fallback: {str(e)}")
                return await self._try_fallback(request, preferred_service)
            raise e
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
            raise AIServiceError(f"Orchestrator error: {str(e)}", "Orchestrator")

    def _select_service(
        self,
        request: AIRequest,
        strategy: RoutingStrategy,
        preferred_service: Optional[str] = None,
    ) -> Optional[str]:
        """Select the best AI service based on strategy."""

        available_services = self._get_healthy_services()

        if not available_services:
            return None

        if strategy == RoutingStrategy.SPECIFIC_MODEL and preferred_service:
            return (
                preferred_service if preferred_service in available_services else None
            )

        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(available_services)

        if strategy == RoutingStrategy.RANDOM:
            return random.choice(available_services)

        if strategy == RoutingStrategy.PERFORMANCE_BASED:
            return self._performance_based_selection(available_services, request)

        if strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._cost_optimized_selection(available_services, request)

        if strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            return self._quality_optimized_selection(available_services, request)

        # Default to first available service
        return available_services[0]

    def _get_healthy_services(self) -> List[str]:
        """Get list of healthy services."""
        return [
            name
            for name, health in self.service_health.items()
            if health in [ServiceHealth.HEALTHY, ServiceHealth.DEGRADED]
        ]

    def _round_robin_selection(self, services: List[str]) -> str:
        """Select service using round-robin strategy."""
        if not services:
            return None

        selected = services[self._round_robin_index % len(services)]
        self._round_robin_index += 1
        return selected

    def _performance_based_selection(
        self, services: List[str], request: AIRequest
    ) -> str:
        """Select service based on performance metrics."""

        best_service = None
        best_score = -1

        for service_name in services:
            metrics = self.service_metrics[service_name]

            # Calculate performance score
            success_rate = metrics["successful_requests"] / max(
                metrics["total_requests"], 1
            )
            response_time_score = max(
                0, 1 - (metrics["avg_response_time"] / 30)
            )  # 30s max
            quality_score = metrics["avg_quality_score"]

            # Weighted performance score
            performance_score = (
                success_rate * 0.4 + response_time_score * 0.3 + quality_score * 0.3
            )

            if performance_score > best_score:
                best_score = performance_score
                best_service = service_name

        return best_service or services[0]

    def _cost_optimized_selection(self, services: List[str], request: AIRequest) -> str:
        """Select the most cost-effective service."""

        # Prefer cheaper models for simple tasks
        if request.task_type in [
            AITaskType.SENTIMENT_ANALYSIS,
            AITaskType.CONTENT_MODERATION,
        ]:
            cheap_services = [s for s in services if "gpt35" in s or "haiku" in s]
            if cheap_services:
                return min(
                    cheap_services, key=lambda s: self.service_metrics[s]["avg_cost"]
                )

        # For complex tasks, balance cost and quality
        best_service = None
        best_value = -1

        for service_name in services:
            metrics = self.service_metrics[service_name]
            cost = metrics["avg_cost"] or 0.01  # Avoid division by zero
            quality = metrics["avg_quality_score"] or 0.5

            value_score = quality / cost  # Quality per dollar

            if value_score > best_value:
                best_value = value_score
                best_service = service_name

        return best_service or services[0]

    def _quality_optimized_selection(
        self, services: List[str], request: AIRequest
    ) -> str:
        """Select service optimized for quality."""

        # For creative tasks, prefer more capable models
        if request.task_type in [
            AITaskType.QUOTE_GENERATION,
            AITaskType.PSYCHOLOGY_ANALYSIS,
        ]:
            premium_services = [
                s for s in services if "gpt4" in s or "sonnet" in s or "opus" in s
            ]
            if premium_services:
                return max(
                    premium_services,
                    key=lambda s: self.service_metrics[s]["avg_quality_score"],
                )

        # Select based on quality score
        return max(services, key=lambda s: self.service_metrics[s]["avg_quality_score"])

    async def _try_fallback(
        self, request: AIRequest, failed_service: str
    ) -> AIResponse:
        """Try fallback services when primary service fails."""

        available_services = [
            name for name in self._get_healthy_services() if name != failed_service
        ]

        if not available_services:
            raise AIServiceError("No fallback services available", "Orchestrator")

        # Try fallback services in order of preference
        for service_name in available_services:
            try:
                service = self.services[service_name]
                response = await service.generate_text(request)

                # Update metrics
                await self._update_service_metrics(service_name, response, success=True)

                logger.info(f"Fallback successful using {service_name}")
                return response

            except Exception as e:
                logger.warning(f"Fallback service {service_name} also failed: {str(e)}")
                await self._update_service_metrics(service_name, None, success=False)
                continue

        raise AIServiceError("All fallback services failed", "Orchestrator")

    async def _update_service_metrics(
        self, service_name: str, response: Optional[AIResponse], success: bool
    ) -> None:
        """Update metrics for a service."""

        metrics = self.service_metrics[service_name]
        metrics["total_requests"] += 1

        if success and response:
            metrics["successful_requests"] += 1

            # Update averages
            if response.processing_time:
                metrics["avg_response_time"] = self._update_average(
                    metrics["avg_response_time"],
                    response.processing_time,
                    metrics["successful_requests"],
                )

            if response.usage.get("estimated_cost"):
                metrics["avg_cost"] = self._update_average(
                    metrics["avg_cost"],
                    response.usage["estimated_cost"],
                    metrics["successful_requests"],
                )

            if response.confidence_score:
                metrics["avg_quality_score"] = self._update_average(
                    metrics["avg_quality_score"],
                    response.confidence_score,
                    metrics["successful_requests"],
                )
        else:
            metrics["failed_requests"] += 1

            # Mark service as degraded if failure rate is high
            failure_rate = metrics["failed_requests"] / metrics["total_requests"]
            if failure_rate > 0.3:  # 30% failure rate
                self.service_health[service_name] = ServiceHealth.DEGRADED
            if failure_rate > 0.7:  # 70% failure rate
                self.service_health[service_name] = ServiceHealth.UNAVAILABLE

        metrics["last_used"] = asyncio.get_event_loop().time()

    def _update_average(
        self, current_avg: float, new_value: float, count: int
    ) -> float:
        """Update running average."""
        if count <= 1:
            return new_value
        return ((current_avg * (count - 1)) + new_value) / count

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services."""

        health_results = {}

        for service_name, service in self.services.items():
            try:
                is_healthy = await service.health_check()
                if is_healthy:
                    self.service_health[service_name] = ServiceHealth.HEALTHY
                    health_results[service_name] = "healthy"
                else:
                    self.service_health[service_name] = ServiceHealth.DEGRADED
                    health_results[service_name] = "degraded"
            except Exception as e:
                self.service_health[service_name] = ServiceHealth.UNAVAILABLE
                health_results[service_name] = f"unavailable: {str(e)}"

        return {
            "overall_health": (
                "healthy"
                if any(h == ServiceHealth.HEALTHY for h in self.service_health.values())
                else "degraded"
            ),
            "services": health_results,
            "total_services": len(self.services),
            "healthy_services": sum(
                1 for h in self.service_health.values() if h == ServiceHealth.HEALTHY
            ),
        }

    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics."""

        total_requests = sum(m["total_requests"] for m in self.service_metrics.values())
        total_successful = sum(
            m["successful_requests"] for m in self.service_metrics.values()
        )

        return {
            "total_requests": total_requests,
            "total_successful": total_successful,
            "overall_success_rate": total_successful / max(total_requests, 1),
            "services": dict(self.service_metrics),
            "health_status": dict(self.service_health),
            "routing_strategy": self.routing_strategy,
            "fallback_enabled": self.fallback_enabled,
        }

    async def generate_quote(
        self,
        prompt: str,
        style: Optional[str] = None,
        tone: Optional[str] = None,
        length: Optional[str] = None,
        context: Optional[str] = None,
        preferred_model: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Generate a quote using the orchestrator."""

        from .base import format_prompt_for_quotes

        formatted_prompt = format_prompt_for_quotes(
            base_prompt=prompt, style=style, tone=tone, length=length, context=context
        )

        request = AIRequest(
            task_type=AITaskType.QUOTE_GENERATION, prompt=formatted_prompt, **kwargs
        )

        strategy = (
            RoutingStrategy.SPECIFIC_MODEL
            if preferred_model
            else RoutingStrategy.QUALITY_OPTIMIZED
        )

        return await self.generate_text(request, strategy, preferred_model)

    async def analyze_text(
        self,
        text: str,
        analysis_type: str = "comprehensive",
        preferred_model: Optional[str] = None,
        **kwargs,
    ) -> AIResponse:
        """Analyze text using the orchestrator."""

        from .base import format_prompt_for_analysis

        formatted_prompt = format_prompt_for_analysis(text, analysis_type)

        task_mapping = {
            "sentiment": AITaskType.SENTIMENT_ANALYSIS,
            "psychology": AITaskType.PSYCHOLOGY_ANALYSIS,
            "comprehensive": AITaskType.TEXT_ANALYSIS,
            "themes": AITaskType.TEXT_ANALYSIS,
            "style": AITaskType.TEXT_ANALYSIS,
        }

        task_type = task_mapping.get(analysis_type, AITaskType.TEXT_ANALYSIS)

        request = AIRequest(task_type=task_type, prompt=formatted_prompt, **kwargs)

        # Use cost-optimized routing for simple analysis tasks
        if analysis_type in ["sentiment"]:
            strategy = RoutingStrategy.COST_OPTIMIZED
        else:
            strategy = RoutingStrategy.PERFORMANCE_BASED

        if preferred_model:
            strategy = RoutingStrategy.SPECIFIC_MODEL

        return await self.generate_text(request, strategy, preferred_model)

    def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """Set the default routing strategy."""
        self.routing_strategy = strategy
        logger.info(f"Routing strategy changed to: {strategy}")

    def enable_fallback(self, enabled: bool = True) -> None:
        """Enable or disable fallback services."""
        self.fallback_enabled = enabled
        logger.info(f"Fallback services {'enabled' if enabled else 'disabled'}")

    def get_available_models(self) -> List[str]:
        """Get list of available AI models."""
        return list(self.services.keys())

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        service = self.services.get(model_name)
        if service:
            return service.get_model_info()
        return None


# Global orchestrator instance
_orchestrator = None


def get_ai_orchestrator() -> AIOrchestrator:
    """Get the global AI orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator
