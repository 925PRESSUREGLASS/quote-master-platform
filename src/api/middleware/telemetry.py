"""
OpenTelemetry FastAPI Middleware Integration
Provides comprehensive request/response tracing and metrics collection.
"""

import time
from typing import Callable
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import extract
from opentelemetry.trace import set_span_in_context
from starlette.middleware.base import BaseHTTPMiddleware

from src.services.ai.monitoring.tracing import (
    add_trace_attributes,
    get_meter,
    get_tracer,
)

logger = structlog.get_logger(__name__)


class OpenTelemetryMiddleware(BaseHTTPMiddleware):
    """Custom OpenTelemetry middleware for enhanced request tracing."""

    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.tracer = get_tracer()
        self.meter = get_meter()

        # Create metrics instruments
        self.request_counter = self.meter.create_counter(
            name="http_requests_total",
            description="Total HTTP requests processed",
            unit="1",
        )

        self.request_duration = self.meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration in seconds",
            unit="s",
        )

        self.response_size = self.meter.create_histogram(
            name="http_response_size_bytes",
            description="HTTP response size in bytes",
            unit="by",
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with comprehensive tracing."""

        # Generate request ID
        request_id = str(uuid4())
        request.state.request_id = request_id

        # Extract trace context from headers
        context = extract(request.headers)

        # Start span for the request
        with self.tracer.start_as_current_span(
            name=f"{request.method} {request.url.path}",
            context=context,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.route": request.url.path,
                "http.user_agent": request.headers.get("user-agent", ""),
                "http.client_ip": self._get_client_ip(request),
                "request.id": request_id,
                "service.name": "quote-master-pro-api",
            },
        ) as span:
            start_time = time.time()

            try:
                # Process request
                response = await call_next(request)

                # Calculate duration
                duration = time.time() - start_time

                # Add response attributes
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_time", duration)

                # Determine response size
                response_size = 0
                if hasattr(response, "body"):
                    response_size = len(response.body) if response.body else 0
                elif hasattr(response, "content_length") and response.content_length:
                    response_size = response.content_length

                span.set_attribute("http.response_size", response_size)

                # Record metrics
                status_class = f"{response.status_code // 100}xx"
                labels = {
                    "method": request.method,
                    "route": request.url.path,
                    "status_code": str(response.status_code),
                    "status_class": status_class,
                }

                self.request_counter.add(1, labels)
                self.request_duration.record(duration, labels)
                if response_size > 0:
                    self.response_size.record(response_size, labels)

                # Set span status based on HTTP status
                if response.status_code >= 400:
                    span.set_status(
                        trace.Status(
                            trace.StatusCode.ERROR, f"HTTP {response.status_code}"
                        )
                    )
                else:
                    span.set_status(trace.Status(trace.StatusCode.OK))

                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id

                # Log request completion
                logger.info(
                    "HTTP request completed",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration * 1000,
                    response_size=response_size,
                )

                return response

            except Exception as e:
                duration = time.time() - start_time

                # Record error in span
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

                # Record error metrics
                error_labels = {
                    "method": request.method,
                    "route": request.url.path,
                    "status_code": "500",
                    "status_class": "5xx",
                    "error_type": type(e).__name__,
                }

                self.request_counter.add(1, error_labels)
                self.request_duration.record(duration, error_labels)

                # Log error
                logger.error(
                    "HTTP request failed",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    error=str(e),
                    error_type=type(e).__name__,
                    duration_ms=duration * 1000,
                )

                raise

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""

        # Check for forwarded headers (common in load balancer setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client address
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"


def setup_opentelemetry_instrumentation(app: FastAPI) -> None:
    """Setup comprehensive OpenTelemetry instrumentation for FastAPI app."""

    # Add custom middleware first
    app.add_middleware(OpenTelemetryMiddleware)

    # Instrument FastAPI with OpenTelemetry
    FastAPIInstrumentor.instrument_app(
        app, excluded_urls="health,metrics,docs,openapi.json,favicon.ico"
    )

    # Startup logging moved to lifespan in main.py
    logger.info("OpenTelemetry instrumentation initialized")

    # Add health check endpoint with tracing
    @app.get("/health")
    async def health_check():
        """Health check endpoint with tracing."""

        tracer = get_tracer()
        with tracer.start_as_current_span("health_check") as span:
            span.set_attribute("health.status", "healthy")
            add_trace_attributes(
                service="quote-master-pro",
                version="1.0.0",
                environment="production",  # Should come from config
            )

            return {
                "status": "healthy",
                "service": "quote-master-pro",
                "version": "1.0.0",
                "timestamp": time.time(),
            }


def add_correlation_id_middleware(app: FastAPI) -> None:
    """Add correlation ID middleware for request tracking."""

    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        """Add correlation ID to requests."""

        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))

        # Store in request state
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response


def setup_request_logging_middleware(app: FastAPI) -> None:
    """Setup structured request logging middleware."""

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        """Log all requests with structured data."""

        start_time = time.time()

        # Extract request info
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
            "content_type": request.headers.get("content-type", ""),
            "content_length": request.headers.get("content-length", 0),
        }

        # Log request start
        logger.info("Request started", **request_info)

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log successful response
            logger.info(
                "Request completed",
                **request_info,
                status_code=response.status_code,
                duration_ms=duration * 1000,
                response_size=getattr(response, "content_length", 0),
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Log error response
            logger.error(
                "Request failed",
                **request_info,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000,
            )

            raise


def setup_comprehensive_instrumentation(app: FastAPI) -> None:
    """Setup all instrumentation middleware in correct order."""

    # 1. Correlation ID middleware (first)
    add_correlation_id_middleware(app)

    # 2. Request logging middleware
    setup_request_logging_middleware(app)

    # 3. OpenTelemetry instrumentation (last)
    setup_opentelemetry_instrumentation(app)
