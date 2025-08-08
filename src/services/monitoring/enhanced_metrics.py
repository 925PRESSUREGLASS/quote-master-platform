"""
Enhanced metrics collection for Quote Master Pro.
Provides comprehensive application and business metrics.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

import structlog
from opentelemetry import metrics
from opentelemetry.metrics import Counter, Histogram, Gauge, UpDownCounter

from src.core.config import get_settings
from src.services.ai.monitoring.tracing import get_meter

logger = structlog.get_logger(__name__)
settings = get_settings()

@dataclass
class BusinessMetrics:
    """Business-level metrics for monitoring."""
    quotes_generated: int = 0
    users_active: int = 0
    revenue_per_hour: float = 0.0
    conversion_rate: float = 0.0
    user_satisfaction_score: float = 0.0

class EnhancedMetricsCollector:
    """Comprehensive metrics collection for Quote Master Pro."""
    
    def __init__(self):
        self.meter = get_meter()
        self._setup_metrics()
        
    def _setup_metrics(self):
        """Setup comprehensive metric instruments."""
        
        # Business metrics
        self.quotes_generated_counter = self.meter.create_counter(
            name="quotes_generated_total",
            description="Total number of quotes generated",
            unit="1"
        )
        
        self.active_users_gauge = self.meter.create_up_down_counter(
            name="active_users_current",
            description="Currently active users",
            unit="1"
        )
        
        self.user_sessions_counter = self.meter.create_counter(
            name="user_sessions_total",
            description="Total user sessions started",
            unit="1"
        )
        
        self.quote_generation_duration = self.meter.create_histogram(
            name="quote_generation_duration_seconds",
            description="Time taken to generate quotes",
            unit="s"
        )
        
        # Cache metrics
        self.cache_operations_counter = self.meter.create_counter(
            name="cache_operations_total",
            description="Cache operations (hit/miss/set)",
            unit="1"
        )
        
        self.cache_hit_ratio_gauge = self.meter.create_gauge(
            name="cache_hit_ratio",
            description="Cache hit ratio",
            unit="1"
        )
        
        # Database metrics
        self.db_query_duration = self.meter.create_histogram(
            name="database_query_duration_seconds",
            description="Database query execution time",
            unit="s"
        )
        
        self.db_connections_active = self.meter.create_up_down_counter(
            name="database_connections_active",
            description="Active database connections",
            unit="1"
        )
        
        self.db_connections_failed = self.meter.create_counter(
            name="db_connections_failed_total",
            description="Failed database connections",
            unit="1"
        )
        
        # Voice processing metrics
        self.voice_uploads_counter = self.meter.create_counter(
            name="voice_uploads_total",
            description="Total voice files uploaded",
            unit="1"
        )
        
        self.voice_processing_duration = self.meter.create_histogram(
            name="voice_processing_duration_seconds",
            description="Voice processing time",
            unit="s"
        )
        
        # API-specific metrics
        self.api_requests_by_endpoint = self.meter.create_counter(
            name="api_requests_by_endpoint_total",
            description="API requests by endpoint",
            unit="1"
        )
        
        self.api_request_size = self.meter.create_histogram(
            name="api_request_size_bytes",
            description="API request payload size",
            unit="by"
        )
        
        # System resource metrics
        self.memory_usage_gauge = self.meter.create_gauge(
            name="system_memory_usage_bytes",
            description="System memory usage",
            unit="by"
        )
        
        # Security metrics
        self.authentication_attempts = self.meter.create_counter(
            name="authentication_attempts_total",
            description="Authentication attempts",
            unit="1"
        )
        
        self.rate_limit_hits = self.meter.create_counter(
            name="rate_limit_hits_total", 
            description="Rate limit violations",
            unit="1"
        )
        
        # Business KPIs
        self.revenue_gauge = self.meter.create_gauge(
            name="revenue_current_hour",
            description="Revenue in current hour",
            unit="USD"
        )
        
        self.customer_satisfaction = self.meter.create_gauge(
            name="customer_satisfaction_score",
            description="Customer satisfaction score (1-5)",
            unit="1"
        )
        
    def record_quote_generated(self, 
                              user_id: Optional[str] = None,
                              provider: Optional[str] = None,
                              processing_time: Optional[float] = None,
                              tokens_used: Optional[int] = None):
        """Record a quote generation event."""
        
        labels = {}
        if provider:
            labels["provider"] = provider
        if user_id:
            labels["user_type"] = "registered" if user_id != "anonymous" else "anonymous"
            
        self.quotes_generated_counter.add(1, labels)
        
        if processing_time:
            self.quote_generation_duration.record(processing_time, labels)
            
        logger.info(
            "Quote generated",
            user_id=user_id,
            provider=provider,
            processing_time=processing_time,
            tokens_used=tokens_used
        )
    
    def record_cache_operation(self, operation: str, hit: bool = False):
        """Record cache operations."""
        
        labels = {
            "operation": operation,
            "result": "hit" if hit else "miss"
        }
        
        self.cache_operations_counter.add(1, labels)
        
    def update_cache_hit_ratio(self, ratio: float):
        """Update current cache hit ratio."""
        self.cache_hit_ratio_gauge.set(ratio)
        
    def record_database_query(self, 
                             query_type: str,
                             duration: float,
                             success: bool = True):
        """Record database query metrics."""
        
        labels = {
            "query_type": query_type,
            "status": "success" if success else "error"
        }
        
        self.db_query_duration.record(duration, labels)
        
        if not success:
            self.db_connections_failed.add(1, {"query_type": query_type})
    
    def record_voice_upload(self, 
                           duration: float,
                           file_size: int,
                           processing_time: Optional[float] = None):
        """Record voice upload and processing."""
        
        labels = {
            "file_size_category": self._get_file_size_category(file_size)
        }
        
        self.voice_uploads_counter.add(1, labels)
        
        if processing_time:
            self.voice_processing_duration.record(processing_time, labels)
    
    def record_api_request(self,
                          endpoint: str,
                          method: str,
                          status_code: int,
                          request_size: int):
        """Record API request metrics."""
        
        labels = {
            "endpoint": endpoint,
            "method": method,
            "status_class": f"{status_code // 100}xx"
        }
        
        self.api_requests_by_endpoint.add(1, labels)
        self.api_request_size.record(request_size, labels)
    
    def record_authentication_attempt(self, 
                                    method: str,
                                    success: bool,
                                    user_type: str = "unknown"):
        """Record authentication attempts."""
        
        labels = {
            "method": method,
            "result": "success" if success else "failure",
            "user_type": user_type
        }
        
        self.authentication_attempts.add(1, labels)
    
    def record_rate_limit_hit(self, 
                             endpoint: str,
                             user_id: Optional[str] = None):
        """Record rate limit violations."""
        
        labels = {
            "endpoint": endpoint,
            "user_type": "registered" if user_id else "anonymous"
        }
        
        self.rate_limit_hits.add(1, labels)
    
    def update_business_metrics(self, metrics: BusinessMetrics):
        """Update business-level metrics."""
        
        self.active_users_gauge.add(metrics.users_active - self._get_previous_active_users())
        self.revenue_gauge.set(metrics.revenue_per_hour)
        self.customer_satisfaction.set(metrics.user_satisfaction_score)
        
        logger.info(
            "Business metrics updated",
            active_users=metrics.users_active,
            quotes_generated=metrics.quotes_generated,
            revenue_per_hour=metrics.revenue_per_hour,
            satisfaction_score=metrics.user_satisfaction_score
        )
    
    def _get_file_size_category(self, size_bytes: int) -> str:
        """Categorize file sizes for metrics."""
        if size_bytes < 1024 * 1024:  # < 1MB
            return "small"
        elif size_bytes < 10 * 1024 * 1024:  # < 10MB
            return "medium"
        else:
            return "large"
    
    def _get_previous_active_users(self) -> int:
        """Get previous active users count for gauge calculation."""
        # This would typically come from a cache or previous reading
        return 0

# Global metrics collector instance
metrics_collector = EnhancedMetricsCollector()

def get_metrics_collector() -> EnhancedMetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector
