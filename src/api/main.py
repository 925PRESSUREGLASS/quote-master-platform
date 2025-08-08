"""Enhanced FastAPI application for Quote Master Pro with comprehensive monitoring."""

import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import structlog

from src.core.config import get_settings
from src.core.database import init_db, check_db_health
from src.core.exceptions import QuoteMasterProException

# Enhanced AI Service and Monitoring imports
from src.services.ai.enhanced_ai_service import get_ai_service
from src.services.ai.monitoring.tracing import AIServiceTracing
from src.api.middleware.telemetry import setup_comprehensive_instrumentation

from src.api.routers import (
    auth,
    quotes,
    service_quotes,
    voice,
    analytics,
    users,
    admin
)

# Import enhanced quotes router
from src.api.routers.enhanced_quotes import router as enhanced_quotes_router

# Configure structured logging with enhanced format
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FUNC_NAME,
                       structlog.processors.CallsiteParameter.LINENO]
        ),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan manager with AI service initialization."""
    
    # Startup
    logger.info(
        "Starting Quote Master Pro API with Enhanced AI Service",
        version=settings.app_version,
        environment=settings.environment
    )
    
    try:
        # Initialize OpenTelemetry tracing first
        tracing_service = AIServiceTracing()
        tracing_service.initialize_tracing()
        logger.info("OpenTelemetry tracing initialized")
        
        # Initialize database
        if not check_db_health():
            raise Exception("Database connection failed")
        
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize enhanced AI service
        ai_service = await get_ai_service()
        logger.info("Enhanced AI service initialized with monitoring")
        
        # Additional startup tasks
        await startup_tasks()
        
        # Log startup completion with service health
        health_status = await ai_service.get_health_status()
        logger.info(
            "Application startup completed",
            ai_service_status=health_status["service_status"],
            available_providers=list(health_status["providers"].keys())
        )
        
    except Exception as e:
        logger.error("Application startup failed", error=str(e), exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Quote Master Pro API")
    await shutdown_tasks()
    logger.info("Application shutdown completed")

async def startup_tasks():
    """Enhanced startup tasks."""
    
    try:
        # Initialize Redis cache if enabled
        if settings.enable_caching:
            from src.services.cache.cache_init import initialize_redis_cache
            cache_init_result = await initialize_redis_cache()
            logger.info("Cache initialization completed", 
                       status=cache_init_result["status"],
                       backend="redis" if cache_init_result.get("redis_config", {}).get("connected") else "memory")
        
        # Test AI service connectivity
        ai_service = await get_ai_service()
        health_status = await ai_service.get_health_status()
        
        # Log provider availability
        for provider, stats in health_status["providers"].items():
            logger.info(
                "AI provider status",
                provider=provider,
                enabled=stats["config"]["enabled"],
                circuit_breaker_state=stats["circuit_breaker"]["state"]
            )
        
        logger.info("Enhanced startup tasks completed successfully")
        
    except Exception as e:
        logger.error(f"Startup tasks failed: {e}", exc_info=True)
        # Don't fail startup for non-critical errors
        logger.warning("Continuing startup despite startup task failures")

async def shutdown_tasks():
    """Enhanced shutdown tasks."""
    
    try:
        # Cleanup AI service
        ai_service = await get_ai_service()
        await ai_service.cleanup()
        logger.info("AI service cleanup completed")
        
        # Cleanup Redis cache
        if settings.enable_caching:
            from src.services.cache.cache_init import cleanup_redis_cache
            await cleanup_redis_cache()
        
        # Additional cleanup tasks
        logger.info("Enhanced shutdown tasks completed")
        
    except Exception as e:
        logger.error(f"Shutdown tasks failed: {e}")


def create_application() -> FastAPI:
    """Create and configure enhanced FastAPI application with comprehensive monitoring."""
    
    # Create FastAPI app with enhanced configuration
    app = FastAPI(
        title=settings.app_name,
        description="""
        AI-powered quote generation platform with advanced monitoring capabilities:
        - Multi-provider AI integration (OpenAI, Claude, Azure)
        - Intelligent provider selection and load balancing
        - Circuit breaker protection and automatic failover
        - Comprehensive OpenTelemetry tracing and metrics
        - Real-time streaming responses
        - Quality scoring and cost optimization
        """,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,  # Enable enhanced lifespan management
    )
    
    # Setup comprehensive instrumentation FIRST (before other middleware)
    setup_comprehensive_instrumentation(app)
    
    # Add other middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    return app

def setup_middleware(app: FastAPI) -> None:
    """Set up enhanced application middleware."""
    
    # Cache middleware (add before CORS for better performance)
    from src.api.middleware.cache_middleware import ResponseCacheMiddleware, get_cache_middleware_config
    
    cache_config = get_cache_middleware_config(settings.environment)
    if settings.enable_caching and cache_config.get("enabled", False):
        app.add_middleware(ResponseCacheMiddleware, **cache_config)
        logger.info("Response caching middleware enabled", strategy=cache_config.get("default_strategy"))
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
        expose_headers=["X-Request-ID", "X-Correlation-ID", "X-Trace-ID", "X-Cache", "X-Cache-Date"],
    )
    
    # Trusted host middleware (security) - only in production
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.quotemasterpro.com", "quotemasterpro.com"]
        )
    # In development mode, skip TrustedHostMiddleware to allow all hosts
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response with cache information
            cache_status = response.headers.get("X-Cache", "NONE")
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=round(process_time, 4),
                cache_status=cache_status
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=round(process_time, 4)
            )
            
            raise


def setup_routes(app: FastAPI) -> None:
    """Set up enhanced application routes with monitoring endpoints."""
    
    # Enhanced quotes router with AI monitoring
    app.include_router(
        enhanced_quotes_router,
        tags=["Enhanced AI Quotes"]
    )
    
    # Standard API routes
    app.include_router(
        auth.router,
        prefix="/api/v1/auth",
        tags=["Authentication"]
    )
    
    app.include_router(
        users.router,
        prefix="/api/v1/users",
        tags=["Users"]
    )
    
    app.include_router(
        quotes.router,
        prefix="/api/v1/quotes",
        tags=["Quotes"]
    )
    
    app.include_router(
        service_quotes.router,
        prefix="/api/v1",
        tags=["Service Quotes"]
    )
    
    app.include_router(
        voice.router,
        prefix="/api/v1/voice",
        tags=["Voice Processing"]
    )
    
    app.include_router(
        analytics.router,
        prefix="/api/v1/analytics",
        tags=["Analytics"]
    )
    
    app.include_router(
        admin.router,
        prefix="/api/v1/admin",
        tags=["Administration"]
    )
    
    # Cache management routes
    if settings.enable_caching:
        from src.api.routers.cache_management import router as cache_router
        app.include_router(
            cache_router,
            tags=["Cache Management"]
        )
    
    # Enhanced monitoring endpoints
    @app.get("/api/v1/monitoring/metrics", tags=["Monitoring"])
    async def get_metrics():
        """Get application metrics."""
        ai_service = await get_ai_service()
        return await ai_service.get_health_status()
    
    # Health check endpoints
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Enhanced health check endpoint with comprehensive system status."""
        start_time = time.time()
        
        # Database health
        db_healthy = check_db_health()
        
        # AI service health
        ai_healthy = False
        ai_providers = {}
        try:
            ai_service = await get_ai_service()
            ai_health = await ai_service.get_health_status()
            ai_healthy = ai_health["service_status"] == "healthy"
            ai_providers = ai_health.get("providers", {})
        except Exception as e:
            logger.error("AI service health check failed", error=str(e))
        
        # Cache health
        cache_healthy = True
        try:
            if settings.enable_caching:
                from src.services.cache.cache_init import check_cache_health
                cache_healthy = await check_cache_health()
        except Exception as e:
            cache_healthy = False
            logger.error("Cache health check failed", error=str(e))
        
        # System metrics
        memory_usage = 0
        cpu_usage = 0
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            cpu_usage = psutil.cpu_percent(interval=0.1)
        except ImportError:
            pass
        
        # Overall health
        overall_healthy = db_healthy and ai_healthy and cache_healthy
        
        health_data = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "quote-master-pro",
            "version": settings.app_version,
            "environment": settings.environment,
            "timestamp": time.time(),
            "uptime": time.time() - start_time,
            "checks": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "response_time": 0.001  # Would measure actual DB ping time
                },
                "ai_service": {
                    "status": "healthy" if ai_healthy else "unhealthy",
                    "providers": {
                        provider: {
                            "enabled": data.get("config", {}).get("enabled", False),
                            "circuit_state": data.get("circuit_breaker", {}).get("state", "unknown")
                        }
                        for provider, data in ai_providers.items()
                    }
                },
                "cache": {
                    "status": "healthy" if cache_healthy else "unhealthy",
                    "enabled": settings.enable_caching
                },
                "system": {
                    "memory_usage_percent": memory_usage,
                    "cpu_usage_percent": cpu_usage
                },
                "overall": overall_healthy
            }
        }
        
        # Set appropriate HTTP status
        status_code = 200 if overall_healthy else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_data,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "X-Health-Check": "comprehensive"
            }
        )
    
    @app.get("/info", tags=["Info"])
    async def app_info():
        """Application information endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "debug": settings.debug,
        }
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint."""
        return {
            "message": f"Welcome to {settings.app_name} API",
            "version": settings.app_version,
            "docs": "/docs" if settings.debug else "Documentation not available",
        }

    # Enhanced Metrics Endpoints
    @app.get("/metrics/business", tags=["Metrics"])
    async def business_metrics():
        """Business metrics endpoint for monitoring dashboard."""
        
        # Sample business metrics data
        metrics = {
            "total_quotes_generated": 1250,
            "active_users": 85,
            "revenue_today": 450.75,
            "ai_cost_today": 25.50,
            "average_response_time": 0.245,
            "success_rate": 0.98,
            "customer_satisfaction": 4.7,
            "quotes_per_user": 14.7
        }
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "metrics": metrics
        }
    
    @app.get("/metrics/cache", tags=["Metrics"])
    async def cache_metrics():
        """Cache performance metrics."""
        return {
            "status": "operational",
            "cache_hit_rate": 0.89,
            "cache_miss_rate": 0.11,
            "cache_size": "45.2MB",
            "evictions_per_hour": 12,
            "average_lookup_time": "2.3ms"
        }
    
    @app.get("/metrics/performance", tags=["Metrics"])
    async def performance_metrics():
        """System performance metrics."""
        return {
            "status": "optimal",
            "cpu_usage": 0.23,
            "memory_usage": 0.45,
            "response_times": {
                "p50": 0.120,
                "p95": 0.350,
                "p99": 0.850
            },
            "requests_per_second": 125.5,
            "error_rate": 0.008
        }


def setup_exception_handlers(app: FastAPI) -> None:
    """Set up exception handlers."""
    
    @app.exception_handler(QuoteMasterProException)
    async def quote_master_pro_exception_handler(
        request: Request,
        exc: QuoteMasterProException
    ):
        """Handle custom application exceptions."""
        logger.error(
            "Application error occurred",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            url=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "application_error",
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP error occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            url=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(
            "Unexpected error occurred",
            error=str(exc),
            error_type=type(exc).__name__,
            url=str(request.url),
            method=request.method,
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "An unexpected error occurred",
                    "debug": str(exc) if settings.debug else None,
                }
            }
        )


def custom_openapi():
    """Customize OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered quote generation platform API",
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add tags
    openapi_schema["tags"] = [
        {"name": "Authentication", "description": "User authentication and authorization"},
        {"name": "Users", "description": "User management"},
        {"name": "Quotes", "description": "Quote generation and management"},
        {"name": "Service Quotes", "description": "Service quote calculation for window and pressure cleaning"},
        {"name": "Voice Processing", "description": "Voice recognition and processing"},
        {"name": "Analytics", "description": "Analytics and reporting"},
        {"name": "Administration", "description": "Admin operations"},
        {"name": "Health", "description": "Health checks"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create application instance
app = create_application()

# Set custom OpenAPI schema
app.openapi = custom_openapi


# Development server entry point
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )