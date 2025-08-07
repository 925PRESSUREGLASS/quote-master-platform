"""
Smart Routing for Quote Master Pro AI Service
Provides intelligent load balancing and provider selection based on performance, cost, and availability.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import heapq
import statistics

import structlog

from .tracing import trace_ai_operation, add_trace_attributes
from .circuit_breaker import circuit_breaker_manager, CircuitBreakerOpenException

logger = structlog.get_logger(__name__)

class RoutingStrategy(Enum):
    """AI provider routing strategies."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_RANDOM = "weighted_random"
    PERFORMANCE_BASED = "performance_based"
    COST_OPTIMIZED = "cost_optimized"
    FAILOVER_PRIORITY = "failover_priority"

@dataclass
class ProviderMetrics:
    """Metrics for an AI provider."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    last_request_time: Optional[datetime] = None
    availability_score: float = 1.0
    recent_response_times: List[float] = field(default_factory=list)
    recent_errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time in seconds."""
        if self.successful_requests == 0:
            return float('inf')
        return self.total_response_time / self.successful_requests
    
    @property
    def average_cost_per_token(self) -> float:
        """Calculate average cost per token."""
        if self.total_tokens_used == 0:
            return 0.0
        return self.total_cost / self.total_tokens_used

@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    name: str
    priority: int = 1  # Lower number = higher priority
    weight: float = 1.0  # For weighted routing
    cost_per_1k_tokens: float = 0.002  # Default pricing
    max_requests_per_minute: int = 100
    max_tokens_per_request: int = 4096
    enabled: bool = True
    fallback_providers: List[str] = field(default_factory=list)

class AIProviderRouter:
    """Intelligent router for AI provider selection and load balancing."""
    
    def __init__(self, providers: List[ProviderConfig]):
        self.providers = {p.name: p for p in providers}
        self.metrics: Dict[str, ProviderMetrics] = {
            p.name: ProviderMetrics() for p in providers
        }
        self.routing_strategy = RoutingStrategy.PERFORMANCE_BASED
        self.current_round_robin_index = 0
        self._lock = asyncio.Lock()
        
        # Rate limiting tracking
        self.request_counts: Dict[str, List[datetime]] = {
            p.name: [] for p in providers
        }
        
    async def select_provider(
        self, 
        request_tokens: int = 0,
        preferred_provider: Optional[str] = None,
        strategy: Optional[RoutingStrategy] = None
    ) -> str:
        """Select the best AI provider based on strategy and current conditions."""
        
        active_strategy = strategy or self.routing_strategy
        
        with trace_ai_operation(
            "provider_selection",
            "router",
            "selection",
            {
                "routing.strategy": active_strategy.value,
                "routing.request_tokens": request_tokens,
                "routing.preferred_provider": preferred_provider
            }
        ) as span:
            
            # Get available providers
            available_providers = await self._get_available_providers(request_tokens)
            
            if not available_providers:
                span.set_attribute("routing.no_providers_available", True)
                raise NoProvidersAvailableException("No AI providers currently available")
            
            # Try preferred provider first if specified and available
            if preferred_provider and preferred_provider in available_providers:
                span.set_attribute("routing.used_preferred_provider", True)
                return preferred_provider
            
            # Select based on strategy
            selected_provider = await self._apply_selection_strategy(
                active_strategy, available_providers, request_tokens
            )
            
            span.set_attribute("routing.selected_provider", selected_provider)
            span.set_attribute("routing.available_count", len(available_providers))
            
            return selected_provider
    
    async def _get_available_providers(self, request_tokens: int) -> List[str]:
        """Get list of currently available providers."""
        available = []
        
        for provider_name, config in self.providers.items():
            if not config.enabled:
                continue
                
            # Check token limits
            if request_tokens > config.max_tokens_per_request:
                continue
                
            # Check rate limits
            if not await self._check_rate_limit(provider_name):
                continue
                
            # Check circuit breaker status
            circuit_breaker = circuit_breaker_manager.get_circuit_breaker(provider_name)
            if circuit_breaker.state.value == "open":
                continue
                
            available.append(provider_name)
        
        return available
    
    async def _check_rate_limit(self, provider_name: str) -> bool:
        """Check if provider is within rate limits."""
        config = self.providers[provider_name]
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.request_counts[provider_name] = [
            timestamp for timestamp in self.request_counts[provider_name]
            if timestamp > minute_ago
        ]
        
        # Check if under limit
        return len(self.request_counts[provider_name]) < config.max_requests_per_minute
    
    async def _apply_selection_strategy(
        self, 
        strategy: RoutingStrategy, 
        available_providers: List[str],
        request_tokens: int
    ) -> str:
        """Apply the specified routing strategy to select a provider."""
        
        if len(available_providers) == 1:
            return available_providers[0]
        
        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self._round_robin_selection(available_providers)
            
        elif strategy == RoutingStrategy.WEIGHTED_RANDOM:
            return self._weighted_random_selection(available_providers)
            
        elif strategy == RoutingStrategy.PERFORMANCE_BASED:
            return await self._performance_based_selection(available_providers)
            
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._cost_optimized_selection(available_providers, request_tokens)
            
        elif strategy == RoutingStrategy.FAILOVER_PRIORITY:
            return self._priority_based_selection(available_providers)
            
        else:
            # Fallback to round robin
            return self._round_robin_selection(available_providers)
    
    def _round_robin_selection(self, providers: List[str]) -> str:
        """Simple round-robin provider selection."""
        provider = providers[self.current_round_robin_index % len(providers)]
        self.current_round_robin_index += 1
        return provider
    
    def _weighted_random_selection(self, providers: List[str]) -> str:
        """Weighted random selection based on provider weights."""
        import random
        
        weights = [self.providers[p].weight for p in providers]
        return random.choices(providers, weights=weights)[0]
    
    async def _performance_based_selection(self, providers: List[str]) -> str:
        """Select provider based on performance metrics."""
        
        provider_scores = []
        
        for provider_name in providers:
            metrics = self.metrics[provider_name]
            
            # Calculate composite performance score (0-1, higher is better)
            success_rate_score = metrics.success_rate
            
            # Response time score (inverse, faster is better)
            if metrics.average_response_time == float('inf'):
                response_time_score = 0.5  # Default for providers with no history
            else:
                # Normalize response time (assuming reasonable range 0.1-10 seconds)
                response_time_score = max(0.0, 1.0 - (metrics.average_response_time / 10.0))
            
            # Availability score
            availability_score = metrics.availability_score
            
            # Combine scores with weights
            composite_score = (
                success_rate_score * 0.4 +
                response_time_score * 0.4 + 
                availability_score * 0.2
            )
            
            provider_scores.append((composite_score, provider_name))
        
        # Sort by score (highest first) and return best provider
        provider_scores.sort(reverse=True)
        return provider_scores[0][1]
    
    def _cost_optimized_selection(self, providers: List[str], request_tokens: int) -> str:
        """Select provider with lowest estimated cost."""
        
        provider_costs = []
        
        for provider_name in providers:
            config = self.providers[provider_name]
            metrics = self.metrics[provider_name]
            
            # Estimate cost for this request
            if metrics.average_cost_per_token > 0:
                # Use historical average
                estimated_cost = metrics.average_cost_per_token * request_tokens
            else:
                # Use configured rate
                estimated_cost = (config.cost_per_1k_tokens / 1000) * request_tokens
            
            # Factor in success rate (failed requests still cost money)
            adjusted_cost = estimated_cost / max(metrics.success_rate, 0.1)
            
            provider_costs.append((adjusted_cost, provider_name))
        
        # Sort by cost (lowest first) and return cheapest
        provider_costs.sort()
        return provider_costs[0][1]
    
    def _priority_based_selection(self, providers: List[str]) -> str:
        """Select provider with highest priority (lowest priority number)."""
        
        provider_priorities = [
            (self.providers[p].priority, p) for p in providers
        ]
        
        # Sort by priority (lowest number = highest priority)
        provider_priorities.sort()
        return provider_priorities[0][1]
    
    async def record_request_start(self, provider_name: str) -> None:
        """Record the start of a request to a provider."""
        
        async with self._lock:
            # Track for rate limiting
            self.request_counts[provider_name].append(datetime.now())
            
            # Update metrics
            metrics = self.metrics[provider_name]
            metrics.total_requests += 1
            metrics.last_request_time = datetime.now()
    
    async def record_request_success(
        self, 
        provider_name: str, 
        response_time: float,
        tokens_used: int,
        estimated_cost: float
    ) -> None:
        """Record a successful request."""
        
        async with self._lock:
            metrics = self.metrics[provider_name]
            metrics.successful_requests += 1
            metrics.total_response_time += response_time
            metrics.total_tokens_used += tokens_used
            metrics.total_cost += estimated_cost
            
            # Update recent response times (keep last 100)
            metrics.recent_response_times.append(response_time)
            if len(metrics.recent_response_times) > 100:
                metrics.recent_response_times.pop(0)
            
            # Update availability score (exponential moving average)
            metrics.availability_score = 0.9 * metrics.availability_score + 0.1 * 1.0
    
    async def record_request_failure(
        self, 
        provider_name: str, 
        error: Exception,
        response_time: float = 0.0
    ) -> None:
        """Record a failed request."""
        
        async with self._lock:
            metrics = self.metrics[provider_name]
            metrics.failed_requests += 1
            
            # Record error details (keep last 50)
            error_info = {
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "response_time": response_time
            }
            
            metrics.recent_errors.append(error_info)
            if len(metrics.recent_errors) > 50:
                metrics.recent_errors.pop(0)
            
            # Update availability score (exponential moving average)
            metrics.availability_score = 0.9 * metrics.availability_score + 0.1 * 0.0
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all providers."""
        
        stats = {}
        
        for provider_name, config in self.providers.items():
            metrics = self.metrics[provider_name]
            circuit_breaker = circuit_breaker_manager.get_circuit_breaker(provider_name)
            
            stats[provider_name] = {
                "config": {
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "weight": config.weight,
                    "cost_per_1k_tokens": config.cost_per_1k_tokens,
                    "max_requests_per_minute": config.max_requests_per_minute
                },
                "metrics": {
                    "total_requests": metrics.total_requests,
                    "success_rate": metrics.success_rate,
                    "average_response_time": metrics.average_response_time,
                    "availability_score": metrics.availability_score,
                    "total_cost": metrics.total_cost,
                    "average_cost_per_token": metrics.average_cost_per_token,
                    "last_request_time": metrics.last_request_time.isoformat() if metrics.last_request_time else None
                },
                "circuit_breaker": {
                    "state": circuit_breaker.state.value,
                    "consecutive_failures": circuit_breaker.metrics.consecutive_failures
                },
                "rate_limiting": {
                    "requests_last_minute": len(self.request_counts[provider_name]),
                    "limit": config.max_requests_per_minute
                }
            }
        
        return stats
    
    async def update_provider_config(self, provider_name: str, **updates) -> bool:
        """Update provider configuration."""
        
        if provider_name not in self.providers:
            return False
        
        config = self.providers[provider_name]
        
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return True

class NoProvidersAvailableException(Exception):
    """Exception raised when no AI providers are available."""
    pass

# Smart routing decorator
def with_smart_routing(
    router: AIProviderRouter,
    strategy: Optional[RoutingStrategy] = None,
    preferred_provider: Optional[str] = None
):
    """Decorator for applying smart routing to AI service calls."""
    
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            
            # Extract request size if available
            request_tokens = kwargs.get('max_tokens', 0)
            
            # Select provider
            provider_name = await router.select_provider(
                request_tokens=request_tokens,
                preferred_provider=preferred_provider,
                strategy=strategy
            )
            
            # Add provider to function call
            kwargs['provider'] = provider_name
            
            # Record request start
            await router.record_request_start(provider_name)
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                response_time = time.time() - start_time
                
                # Estimate tokens and cost (provider-specific logic needed)
                tokens_used = getattr(result, 'usage', {}).get('total_tokens', request_tokens)
                provider_config = router.providers[provider_name]
                estimated_cost = (provider_config.cost_per_1k_tokens / 1000) * tokens_used
                
                await router.record_request_success(
                    provider_name, response_time, tokens_used, estimated_cost
                )
                
                return result
                
            except Exception as e:
                response_time = time.time() - start_time
                await router.record_request_failure(provider_name, e, response_time)
                raise
        
        return wrapper
    
    return decorator
