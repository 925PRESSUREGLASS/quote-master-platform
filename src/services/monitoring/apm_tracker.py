"""
Application Performance Monitoring integration.
Provides deep insights into application performance and user experience.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import asynccontextmanager

import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from src.services.monitoring.enhanced_metrics import get_metrics_collector

logger = structlog.get_logger(__name__)

@dataclass
class PerformanceProfile:
    """Performance profiling data."""
    endpoint: str
    duration: float
    memory_usage: int
    cpu_usage: float
    database_queries: int
    cache_operations: int
    external_calls: int

class APMTracker:
    """Application Performance Monitoring tracker."""
    
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.metrics = get_metrics_collector()
        self.active_requests: Dict[str, Dict] = {}
        
    @asynccontextmanager
    async def track_request(self, 
                           endpoint: str,
                           user_id: Optional[str] = None,
                           correlation_id: Optional[str] = None):
        """Track a complete request lifecycle."""
        
        request_id = correlation_id or f"req_{int(time.time() * 1000)}"
        start_time = time.time()
        
        # Start tracking
        self.active_requests[request_id] = {
            "endpoint": endpoint,
            "user_id": user_id,
            "start_time": start_time,
            "db_queries": 0,
            "cache_ops": 0,
            "external_calls": 0,
            "memory_start": self._get_memory_usage()
        }
        
        with self.tracer.start_as_current_span(f"request_{endpoint}") as span:
            span.set_attribute("http.endpoint", endpoint)
            span.set_attribute("user.id", user_id or "anonymous")
            span.set_attribute("request.id", request_id)
            
            try:
                yield request_id
                
                # Success - record metrics
                duration = time.time() - start_time
                self._record_successful_request(request_id, duration)
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Error - record failure
                duration = time.time() - start_time
                self._record_failed_request(request_id, duration, e)
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
                
            finally:
                # Cleanup
                if request_id in self.active_requests:
                    del self.active_requests[request_id]
    
    def track_database_query(self, 
                           request_id: str,
                           query_type: str,
                           duration: float):
        """Track a database query within a request."""
        
        if request_id in self.active_requests:
            self.active_requests[request_id]["db_queries"] += 1
            
        self.metrics.record_database_query(query_type, duration)
        
        with self.tracer.start_as_current_span("db_query") as span:
            span.set_attribute("db.query_type", query_type)
            span.set_attribute("db.duration", duration)
    
    def track_cache_operation(self,
                            request_id: str,
                            operation: str,
                            hit: bool):
        """Track a cache operation within a request."""
        
        if request_id in self.active_requests:
            self.active_requests[request_id]["cache_ops"] += 1
            
        self.metrics.record_cache_operation(operation, hit)
    
    def track_external_call(self,
                          request_id: str,
                          service: str,
                          duration: float,
                          success: bool):
        """Track external service calls."""
        
        if request_id in self.active_requests:
            self.active_requests[request_id]["external_calls"] += 1
            
        with self.tracer.start_as_current_span(f"external_call_{service}") as span:
            span.set_attribute("external.service", service)
            span.set_attribute("external.duration", duration)
            span.set_attribute("external.success", success)
    
    async def track_quote_generation(self,
                                   request_id: str,
                                   provider: str,
                                   prompt_tokens: int,
                                   completion_tokens: int,
                                   cost: float):
        """Track AI quote generation with detailed metrics."""
        
        with self.tracer.start_as_current_span("ai_quote_generation") as span:
            span.set_attribute("ai.provider", provider)
            span.set_attribute("ai.prompt_tokens", prompt_tokens)
            span.set_attribute("ai.completion_tokens", completion_tokens)
            span.set_attribute("ai.cost", cost)
            
            # Record business metric
            total_tokens = prompt_tokens + completion_tokens
            processing_time = span.get_span_context().span_id  # Use span timing
            
            self.metrics.record_quote_generated(
                user_id=self.active_requests.get(request_id, {}).get("user_id"),
                provider=provider,
                tokens_used=total_tokens
            )
    
    def get_performance_profile(self, request_id: str) -> Optional[PerformanceProfile]:
        """Get performance profile for a request."""
        
        if request_id not in self.active_requests:
            return None
            
        req_data = self.active_requests[request_id]
        current_time = time.time()
        
        return PerformanceProfile(
            endpoint=req_data["endpoint"],
            duration=current_time - req_data["start_time"],
            memory_usage=self._get_memory_usage() - req_data["memory_start"],
            cpu_usage=self._get_cpu_usage(),
            database_queries=req_data["db_queries"],
            cache_operations=req_data["cache_ops"],
            external_calls=req_data["external_calls"]
        )
    
    def get_slow_requests(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Get currently slow-running requests."""
        
        slow_requests = []
        current_time = time.time()
        
        for req_id, req_data in self.active_requests.items():
            duration = current_time - req_data["start_time"]
            
            if duration > threshold:
                slow_requests.append({
                    "request_id": req_id,
                    "endpoint": req_data["endpoint"],
                    "duration": duration,
                    "user_id": req_data.get("user_id")
                })
        
        return slow_requests
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        
        return {
            "active_requests": len(self.active_requests),
            "slow_requests": len(self.get_slow_requests()),
            "avg_response_time": await self._calculate_avg_response_time(),
            "error_rate": await self._calculate_error_rate(),
            "throughput": await self._calculate_throughput(),
            "resource_usage": {
                "memory": self._get_memory_usage(),
                "cpu": self._get_cpu_usage()
            }
        }
    
    def _record_successful_request(self, request_id: str, duration: float):
        """Record successful request metrics."""
        
        req_data = self.active_requests.get(request_id, {})
        
        logger.info(
            "Request completed successfully",
            request_id=request_id,
            endpoint=req_data.get("endpoint"),
            duration=duration,
            db_queries=req_data.get("db_queries", 0),
            cache_ops=req_data.get("cache_ops", 0),
            external_calls=req_data.get("external_calls", 0)
        )
    
    def _record_failed_request(self, request_id: str, duration: float, error: Exception):
        """Record failed request metrics."""
        
        req_data = self.active_requests.get(request_id, {})
        
        logger.error(
            "Request failed",
            request_id=request_id,
            endpoint=req_data.get("endpoint"),
            duration=duration,
            error=str(error),
            error_type=type(error).__name__
        )
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            return 0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
    
    async def _calculate_avg_response_time(self) -> float:
        """Calculate average response time from recent data."""
        # This would typically query metrics backend
        return 0.25  # Placeholder
    
    async def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        # This would typically query metrics backend
        return 0.02  # Placeholder
    
    async def _calculate_throughput(self) -> float:
        """Calculate requests per second."""
        # This would typically query metrics backend
        return 120.5  # Placeholder

# Global APM tracker instance
apm_tracker = APMTracker()

def get_apm_tracker() -> APMTracker:
    """Get the global APM tracker instance."""
    return apm_tracker
