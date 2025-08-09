"""
Performance monitoring middleware for Quote Master Pro.
Tracks response times, request rates, and system performance metrics.
"""

import asyncio
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

import psutil
from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ACTIVE_REQUESTS = Gauge("http_requests_active", "Number of active HTTP requests")

SYSTEM_CPU_USAGE = Gauge("system_cpu_usage_percent", "System CPU usage percentage")

SYSTEM_MEMORY_USAGE = Gauge("system_memory_usage_bytes", "System memory usage in bytes")

QUOTE_GENERATION_DURATION = Histogram(
    "quote_generation_duration_seconds",
    "Quote generation duration in seconds",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

QUOTE_GENERATION_COUNT = Counter(
    "quote_generations_total",
    "Total quote generations",
    ["service_type", "suburb", "status"],
)

PRICING_CALCULATION_DURATION = Histogram(
    "pricing_calculation_duration_seconds",
    "Pricing calculation duration in seconds",
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5],
)

DATABASE_QUERY_DURATION = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track performance metrics and system resource usage.
    """

    def __init__(self, app, enable_detailed_logging: bool = False):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
        self.process = psutil.Process(os.getpid())

        # Start system monitoring task
        asyncio.create_task(self._monitor_system_resources())

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track performance metrics"""
        start_time = time.time()

        # Increment active requests counter
        ACTIVE_REQUESTS.inc()

        # Extract endpoint information
        method = request.method
        endpoint = self._get_endpoint_name(request)

        try:
            # Process the request
            response = await call_next(request)
            status_code = str(response.status_code)

        except Exception as e:
            logger.error(f"Request processing error: {str(e)}")
            status_code = "500"
            raise

        finally:
            # Calculate request duration
            duration = time.time() - start_time

            # Update metrics
            REQUEST_COUNT.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()

            REQUEST_DURATION.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).observe(duration)

            # Decrement active requests counter
            ACTIVE_REQUESTS.dec()

            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Process-Time"] = f"{time.time()}"

            # Detailed logging for slow requests
            if self.enable_detailed_logging and duration > 1.0:
                logger.warning(
                    f"Slow request detected: {method} {endpoint} "
                    f"took {duration:.3f}s (status: {status_code})"
                )

            # Track quote-specific metrics
            if endpoint.startswith("/api/v1/quotes") and method == "POST":
                await self._track_quote_metrics(request, duration, status_code)

        return response

    def _get_endpoint_name(self, request: Request) -> str:
        """Extract meaningful endpoint name from request"""
        path = request.url.path

        # Normalize paths with IDs
        import re

        # Replace UUIDs and numeric IDs with placeholders
        path = re.sub(r"/[0-9a-f-]{36}", "/{id}", path)  # UUID
        path = re.sub(r"/\d+", "/{id}", path)  # Numeric ID

        return path

    async def _track_quote_metrics(
        self, request: Request, duration: float, status_code: str
    ):
        """Track quote-specific performance metrics"""
        try:
            if hasattr(request, "_json"):
                body = await request.json()

                service_type = body.get("service_type", "unknown")
                suburb = body.get("suburb", "unknown")

                # Track quote generation
                QUOTE_GENERATION_DURATION.observe(duration)
                QUOTE_GENERATION_COUNT.labels(
                    service_type=service_type,
                    suburb=suburb,
                    status="success" if status_code.startswith("2") else "error",
                ).inc()

        except Exception as e:
            logger.debug(f"Error tracking quote metrics: {str(e)}")

    async def _monitor_system_resources(self):
        """Background task to monitor system resources"""
        while True:
            try:
                # CPU usage
                cpu_percent = self.process.cpu_percent()
                SYSTEM_CPU_USAGE.set(cpu_percent)

                # Memory usage
                memory_info = self.process.memory_info()
                SYSTEM_MEMORY_USAGE.set(memory_info.rss)

                # Log high resource usage
                if cpu_percent > 80:
                    logger.warning(f"High CPU usage detected: {cpu_percent:.1f}%")

                if memory_info.rss > 1024 * 1024 * 1024:  # 1GB
                    memory_mb = memory_info.rss / 1024 / 1024
                    logger.warning(f"High memory usage detected: {memory_mb:.1f}MB")

            except Exception as e:
                logger.error(f"Error monitoring system resources: {str(e)}")

            # Check every 30 seconds
            await asyncio.sleep(30)


class PerformanceTracker:
    """
    Context manager for tracking specific operation performance.
    """

    def __init__(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        self.operation_name = operation_name
        self.labels = labels or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time

            # Track specific operation metrics
            if self.operation_name == "pricing_calculation":
                PRICING_CALCULATION_DURATION.observe(duration)
            elif self.operation_name == "database_query":
                DATABASE_QUERY_DURATION.labels(
                    operation=self.labels.get("operation", "unknown"),
                    table=self.labels.get("table", "unknown"),
                ).observe(duration)

            # Log slow operations
            if duration > 5.0:  # 5 second threshold
                logger.warning(
                    f"Slow {self.operation_name} detected: {duration:.3f}s "
                    f"(labels: {self.labels})"
                )


def track_pricing_calculation():
    """Context manager for tracking pricing calculation performance"""
    return PerformanceTracker("pricing_calculation")


def track_database_query(operation: str, table: str):
    """Context manager for tracking database query performance"""
    return PerformanceTracker(
        "database_query", {"operation": operation, "table": table}
    )


async def track_ai_service_performance(service_call, provider: str, operation: str):
    """Decorator to track AI service performance"""
    ai_service_duration = Histogram(
        "ai_service_duration_seconds",
        "AI service call duration",
        ["provider", "operation", "status"],
        buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
    )

    ai_service_count = Counter(
        "ai_service_requests_total",
        "Total AI service requests",
        ["provider", "operation", "status"],
    )

    start_time = time.time()
    status = "success"

    try:
        result = await service_call
        return result
    except Exception as e:
        status = "error"
        logger.error(f"AI service error ({provider}/{operation}): {str(e)}")
        raise
    finally:
        duration = time.time() - start_time

        ai_service_duration.labels(
            provider=provider, operation=operation, status=status
        ).observe(duration)

        ai_service_count.labels(
            provider=provider, operation=operation, status=status
        ).inc()


class PerformanceAlert:
    """
    Simple performance alerting system.
    """

    @staticmethod
    def check_response_time_alert(duration: float, threshold: float = 5.0):
        """Check if response time exceeds threshold"""
        if duration > threshold:
            logger.error(
                f"PERFORMANCE ALERT: Response time {duration:.3f}s "
                f"exceeds threshold {threshold}s"
            )
            return True
        return False

    @staticmethod
    def check_memory_usage_alert(memory_mb: float, threshold: float = 1024.0):
        """Check if memory usage exceeds threshold"""
        if memory_mb > threshold:
            logger.error(
                f"PERFORMANCE ALERT: Memory usage {memory_mb:.1f}MB "
                f"exceeds threshold {threshold}MB"
            )
            return True
        return False

    @staticmethod
    def check_cpu_usage_alert(cpu_percent: float, threshold: float = 85.0):
        """Check if CPU usage exceeds threshold"""
        if cpu_percent > threshold:
            logger.error(
                f"PERFORMANCE ALERT: CPU usage {cpu_percent:.1f}% "
                f"exceeds threshold {threshold}%"
            )
            return True
        return False


# Utility functions for performance monitoring
def get_current_memory_usage() -> float:
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def get_current_cpu_usage() -> float:
    """Get current CPU usage percentage"""
    process = psutil.Process(os.getpid())
    return process.cpu_percent()


def log_performance_summary():
    """Log current performance summary"""
    memory_mb = get_current_memory_usage()
    cpu_percent = get_current_cpu_usage()

    logger.info(
        f"Performance Summary - "
        f"Memory: {memory_mb:.1f}MB, "
        f"CPU: {cpu_percent:.1f}%"
    )
