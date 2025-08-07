"""
Circuit Breaker Implementation for Quote Master Pro AI Service
Provides intelligent failover and resilience patterns for AI provider calls.
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncio
from functools import wraps

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

from .tracing import trace_ai_operation, add_trace_attributes, record_exception

logger = structlog.get_logger(__name__)

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, requests blocked
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before trying half-open
    success_threshold: int = 3   # Successes to close from half-open
    timeout_seconds: float = 30.0  # Request timeout
    
@dataclass  
class CircuitMetrics:
    """Circuit breaker metrics tracking."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=50))

class AIProviderCircuitBreaker:
    """Circuit breaker for AI provider resilience."""
    
    def __init__(self, provider_name: str, config: CircuitBreakerConfig):
        self.provider_name = provider_name
        self.config = config
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.state_change_time = datetime.now()
        self._lock = asyncio.Lock()
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        
        with trace_ai_operation(
            "circuit_breaker_call",
            self.provider_name,
            kwargs.get('model', 'unknown'),
            {
                "circuit.state": self.state.value,
                "circuit.failure_count": self.metrics.consecutive_failures
            }
        ) as span:
            
            async with self._lock:
                # Check if circuit should be opened
                if self.state == CircuitState.CLOSED and self._should_open():
                    await self._open_circuit()
                
                # Check if circuit should move to half-open
                elif self.state == CircuitState.OPEN and self._should_attempt_reset():
                    await self._half_open_circuit()
                
                # Block requests if circuit is open
                if self.state == CircuitState.OPEN:
                    span.set_attribute("circuit.request_blocked", True)
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker for {self.provider_name} is OPEN"
                    )
            
            # Execute the function call
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                await self._record_success(duration)
                
                span.set_attribute("circuit.call_success", True)
                span.set_attribute("circuit.response_time_ms", duration * 1000)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                await self._record_failure(e, duration)
                
                span.set_attribute("circuit.call_success", False)
                span.set_attribute("circuit.error_type", type(e).__name__)
                record_exception(e)
                
                raise

    async def _record_success(self, duration: float) -> None:
        """Record successful request."""
        async with self._lock:
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.metrics.consecutive_failures = 0
            self.metrics.consecutive_successes += 1
            self.metrics.last_success_time = datetime.now()
            self.metrics.recent_response_times.append(duration)
            
            # Close circuit if in half-open state with enough successes
            if (self.state == CircuitState.HALF_OPEN and 
                self.metrics.consecutive_successes >= self.config.success_threshold):
                await self._close_circuit()

    async def _record_failure(self, exception: Exception, duration: float) -> None:
        """Record failed request."""
        async with self._lock:
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
            self.metrics.last_failure_time = datetime.now()
            
            failure_info = {
                "timestamp": datetime.now().isoformat(),
                "error": str(exception),
                "error_type": type(exception).__name__,
                "duration": duration
            }
            self.metrics.recent_failures.append(failure_info)

    def _should_open(self) -> bool:
        """Check if circuit should be opened."""
        return self.metrics.consecutive_failures >= self.config.failure_threshold

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset to half-open."""
        if not self.metrics.last_failure_time:
            return False
            
        time_since_failure = datetime.now() - self.metrics.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout

    async def _open_circuit(self) -> None:
        """Open the circuit breaker."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.state_change_time = datetime.now()
            
            logger.warning(
                "Circuit breaker opened",
                provider=self.provider_name,
                consecutive_failures=self.metrics.consecutive_failures,
                total_failures=self.metrics.failed_requests
            )

    async def _half_open_circuit(self) -> None:
        """Move circuit to half-open state."""
        if self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.HALF_OPEN
            self.state_change_time = datetime.now()
            self.metrics.consecutive_successes = 0
            
            logger.info(
                "Circuit breaker half-opened for testing",
                provider=self.provider_name
            )

    async def _close_circuit(self) -> None:
        """Close the circuit breaker."""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.state_change_time = datetime.now()
            
            logger.info(
                "Circuit breaker closed - service recovered", 
                provider=self.provider_name,
                consecutive_successes=self.metrics.consecutive_successes
            )

    def get_health_status(self) -> Dict[str, Any]:
        """Get current circuit breaker health status."""
        success_rate = 0.0
        if self.metrics.total_requests > 0:
            success_rate = self.metrics.successful_requests / self.metrics.total_requests

        avg_response_time = 0.0
        if self.metrics.recent_response_times:
            avg_response_time = sum(self.metrics.recent_response_times) / len(self.metrics.recent_response_times)

        return {
            "provider": self.provider_name,
            "state": self.state.value,
            "state_duration_seconds": (datetime.now() - self.state_change_time).total_seconds(),
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "success_rate": success_rate,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "avg_response_time_ms": avg_response_time * 1000,
                "recent_failure_count": len(self.metrics.recent_failures)
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold
            }
        }

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass

class AIServiceCircuitBreakerManager:
    """Manages circuit breakers for multiple AI providers."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, AIProviderCircuitBreaker] = {}
        self.default_config = CircuitBreakerConfig()
        
    def get_circuit_breaker(
        self, 
        provider_name: str, 
        config: Optional[CircuitBreakerConfig] = None
    ) -> AIProviderCircuitBreaker:
        """Get or create circuit breaker for provider."""
        
        if provider_name not in self.circuit_breakers:
            breaker_config = config or self.default_config
            self.circuit_breakers[provider_name] = AIProviderCircuitBreaker(
                provider_name, breaker_config
            )
            
        return self.circuit_breakers[provider_name]
    
    async def call_with_circuit_breaker(
        self,
        provider_name: str,
        func: Callable,
        *args,
        config: Optional[CircuitBreakerConfig] = None,
        **kwargs
    ) -> Any:
        """Execute function call with circuit breaker protection."""
        
        circuit_breaker = self.get_circuit_breaker(provider_name, config)
        return await circuit_breaker.call(func, *args, **kwargs)
    
    def get_all_health_status(self) -> Dict[str, Any]:
        """Get health status for all circuit breakers."""
        return {
            name: breaker.get_health_status() 
            for name, breaker in self.circuit_breakers.items()
        }
    
    async def reset_circuit_breaker(self, provider_name: str) -> bool:
        """Manually reset a circuit breaker."""
        if provider_name in self.circuit_breakers:
            breaker = self.circuit_breakers[provider_name]
            async with breaker._lock:
                await breaker._close_circuit()
                breaker.metrics = CircuitMetrics()  # Reset metrics
            return True
        return False

# Global circuit breaker manager instance
circuit_breaker_manager = AIServiceCircuitBreakerManager()

def with_circuit_breaker(
    provider_name: str, 
    config: Optional[CircuitBreakerConfig] = None
):
    """Decorator for applying circuit breaker to functions."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await circuit_breaker_manager.call_with_circuit_breaker(
                provider_name, func, *args, config=config, **kwargs
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Convert sync function to async for circuit breaker
            async def async_func():
                return func(*args, **kwargs)
            
            return asyncio.run(
                circuit_breaker_manager.call_with_circuit_breaker(
                    provider_name, async_func, config=config
                )
            )
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Retry decorator with circuit breaker integration
def with_intelligent_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: int = 2
):
    """Retry decorator with exponential backoff and circuit breaker awareness."""
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=base_delay,
            max=max_delay,
            exp_base=exponential_base
        ),
        retry=retry_if_exception_type((
            ConnectionError,
            TimeoutError,
            # Add specific AI provider exceptions here
        )),
        reraise=True
    )
