"""
OpenTelemetry Distributed Tracing for Quote Master Pro AI Service
Provides comprehensive tracing capabilities for AI provider requests and service operations.
"""

import logging
import os
import time
from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable
from functools import wraps

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global tracer and meter instances
_tracer = None
_meter = None

class AIServiceTracing:
    """Centralized OpenTelemetry tracing configuration for AI services."""
    
    def __init__(self):
        self.service_name = "quote-master-pro-ai-service"
        self.service_version = "1.0.0"
        self.tracer = None
        self.meter = None
        self.initialized = False
        
    def initialize_tracing(self) -> None:
        """Initialize OpenTelemetry tracing and metrics."""
        
        if self.initialized:
            return
            
        try:
            # Create resource with service information
            resource = Resource.create({
                SERVICE_NAME: self.service_name,
                SERVICE_VERSION: self.service_version,
                "service.instance.id": os.getenv("HOSTNAME", "local"),
                "deployment.environment": settings.environment,
            })
            
            # Configure trace provider
            trace_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(trace_provider)
            
            # Configure exporters based on environment
            if settings.environment == "production" or os.getenv("USE_OTLP_COLLECTOR", "false").lower() == "true":
                # Production: Export to OTLP collector
                otlp_exporter = OTLPSpanExporter(
                    endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4317"),
                    headers={}  # Add authentication if needed
                )
                trace_provider.add_span_processor(
                    BatchSpanProcessor(otlp_exporter)
                )
                logger.info("Using OTLP exporter for traces")
            else:
                # Development: Export to console
                console_exporter = ConsoleSpanExporter()
                trace_provider.add_span_processor(
                    BatchSpanProcessor(console_exporter)
                )
                logger.info("Using console exporter for traces")
            
            # Configure metrics
            metric_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter() if settings.environment != "production" 
                else OTLPMetricExporter(),
                export_interval_millis=30000
            )
            
            metrics_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader]
            )
            metrics.set_meter_provider(metrics_provider)
            
            # Set global propagators for distributed tracing
            set_global_textmap(B3MultiFormat())
            
            # Get tracer and meter instances
            self.tracer = trace.get_tracer(self.service_name, self.service_version)
            self.meter = metrics.get_meter(self.service_name, self.service_version)
            
            # Instrument common libraries
            self._instrument_libraries()
            
            self.initialized = True
            logger.info(f"OpenTelemetry tracing initialized for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry tracing: {e}")
            # Fallback to noop implementations
            self.tracer = trace.NoOpTracer()
            self.meter = metrics.NoOpMeter("fallback")
    
    def _instrument_libraries(self) -> None:
        """Automatically instrument common libraries."""
        try:
            # Instrument HTTP requests
            RequestsInstrumentor().instrument()
            
            # Instrument SQLAlchemy if available
            SQLAlchemyInstrumentor().instrument()
            
            logger.info("Automatic instrumentation enabled for HTTP and database operations")
            
        except Exception as e:
            logger.warning(f"Could not enable automatic instrumentation: {e}")
    
    def get_tracer(self):
        """Get the configured tracer instance."""
        if not self.initialized:
            self.initialize_tracing()
        return self.tracer
    
    def get_meter(self):
        """Get the configured meter instance."""
        if not self.initialized:
            self.initialize_tracing()
        return self.meter

# Global instance
_tracing_service = AIServiceTracing()

def get_tracer():
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = _tracing_service.get_tracer()
    return _tracer

def get_meter():
    """Get the global meter instance.""" 
    global _meter
    if _meter is None:
        _meter = _tracing_service.get_meter()
    return _meter

@contextmanager
def trace_ai_operation(
    operation_name: str,
    provider: str,
    model: str,
    attributes: Optional[Dict[str, Any]] = None
):
    """Context manager for tracing AI operations with comprehensive metadata."""
    
    tracer = get_tracer()
    span_attributes = {
        "ai.provider": provider,
        "ai.model": model,
        "ai.operation": operation_name,
        "service.component": "ai_service"
    }
    
    if attributes:
        span_attributes.update(attributes)
    
    with tracer.start_as_current_span(
        f"ai.{operation_name}",
        attributes=span_attributes
    ) as span:
        start_time = time.time()
        
        try:
            yield span
            span.set_status(trace.Status(trace.StatusCode.OK))
            
        except Exception as e:
            span.set_status(
                trace.Status(
                    trace.StatusCode.ERROR,
                    description=str(e)
                )
            )
            span.record_exception(e)
            raise
            
        finally:
            duration = time.time() - start_time
            span.set_attribute("ai.duration_ms", duration * 1000)

def trace_ai_request(func: Callable) -> Callable:
    """Decorator for tracing AI provider requests."""
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Extract tracing info from function context
        operation_name = func.__name__
        provider = getattr(args[0], 'provider_name', 'unknown') if args else 'unknown'
        model = kwargs.get('model', getattr(args[0], 'model_name', 'unknown'))
        
        attributes = {
            "ai.request.tokens": kwargs.get('max_tokens', 0),
            "ai.request.temperature": kwargs.get('temperature', 0.0),
        }
        
        with trace_ai_operation(operation_name, provider, model, attributes) as span:
            result = await func(*args, **kwargs)
            
            # Add response attributes if available
            if hasattr(result, 'usage'):
                span.set_attribute("ai.response.tokens.total", getattr(result.usage, 'total_tokens', 0))
                span.set_attribute("ai.response.tokens.prompt", getattr(result.usage, 'prompt_tokens', 0))
                span.set_attribute("ai.response.tokens.completion", getattr(result.usage, 'completion_tokens', 0))
            
            return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Extract tracing info from function context
        operation_name = func.__name__
        provider = getattr(args[0], 'provider_name', 'unknown') if args else 'unknown'
        model = kwargs.get('model', getattr(args[0], 'model_name', 'unknown'))
        
        attributes = {
            "ai.request.tokens": kwargs.get('max_tokens', 0),
            "ai.request.temperature": kwargs.get('temperature', 0.0),
        }
        
        with trace_ai_operation(operation_name, provider, model, attributes) as span:
            result = func(*args, **kwargs)
            
            # Add response attributes if available
            if hasattr(result, 'usage'):
                span.set_attribute("ai.response.tokens.total", getattr(result.usage, 'total_tokens', 0))
                span.set_attribute("ai.response.tokens.prompt", getattr(result.usage, 'prompt_tokens', 0))
                span.set_attribute("ai.response.tokens.completion", getattr(result.usage, 'completion_tokens', 0))
            
            return result
    
    # Return appropriate wrapper based on function type
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def add_trace_attributes(**attributes):
    """Add custom attributes to the current span."""
    current_span = trace.get_current_span()
    if current_span:
        for key, value in attributes.items():
            current_span.set_attribute(key, value)

def record_exception(exception: Exception, attributes: Optional[Dict[str, Any]] = None):
    """Record an exception in the current span."""
    current_span = trace.get_current_span()
    if current_span:
        current_span.record_exception(exception, attributes or {})
        current_span.set_status(
            trace.Status(trace.StatusCode.ERROR, description=str(exception))
        )

# Initialize tracing on module import if enabled
if os.getenv("ENABLE_TRACING", "true").lower() == "true":
    _tracing_service.initialize_tracing()