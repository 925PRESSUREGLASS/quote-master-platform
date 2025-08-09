"""Enhanced FastAPI application for Quote Master Pro with comprehensive monitoring."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from src.api.middleware.telemetry import setup_comprehensive_instrumentation
from src.api.routers import (
    admin,
    analytics,
    auth,
    quotes,
    service_quotes,
    simple_quotes,
    users,
    voice,
)

# Import enhanced quotes router
from src.api.routers.enhanced_quotes import router as enhanced_quotes_router
from src.core.config import get_settings
from src.core.database import check_db_health, init_db
from src.core.exceptions import QuoteMasterProException

# Enhanced AI Service and Monitoring imports
from src.services.ai.enhanced_ai_service import get_ai_service
from src.services.ai.monitoring.tracing import AIServiceTracing

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
            parameters=[
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.JSONRenderer(),
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
        environment=settings.environment,
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
            available_providers=list(health_status["providers"].keys()),
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
        # Test AI service connectivity
        ai_service = await get_ai_service()
        health_status = await ai_service.get_health_status()

        # Log provider availability
        for provider, stats in health_status["providers"].items():
            logger.info(
                "AI provider status",
                provider=provider,
                enabled=stats["config"]["enabled"],
                circuit_breaker_state=stats["circuit_breaker"]["state"],
            )

        # Initialize cache if enabled
        if settings.enable_caching:
            logger.info("Redis cache enabled and initialized")

        logger.info("Enhanced startup tasks completed successfully")

    except Exception as e:
        logger.error("Startup tasks failed", error=str(e), exc_info=True)
        # Don't fail startup for non-critical errors
        logger.warning("Continuing startup despite startup task failures")


async def shutdown_tasks():
    """Enhanced shutdown tasks."""

    try:
        # Cleanup AI service
        ai_service = await get_ai_service()
        await ai_service.cleanup()
        logger.info("AI service cleanup completed")

        # Additional cleanup tasks
        logger.info("Enhanced shutdown tasks completed")

    except Exception as e:
        logger.error("Shutdown tasks failed", error=str(e))


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

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
        expose_headers=["X-Request-ID", "X-Correlation-ID", "X-Trace-ID"],
    )

    # Trusted host middleware (security)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.quotemasterpro.com", "quotemasterpro.com"],
        )

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

            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=round(process_time, 4),
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
                process_time=round(process_time, 4),
            )

            raise


def setup_routes(app: FastAPI) -> None:
    """Set up enhanced application routes with monitoring endpoints."""

    # Enhanced quotes router with AI monitoring
    app.include_router(enhanced_quotes_router, tags=["Enhanced AI Quotes"])

    # Standard API routes
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    # Legacy route prefix for backward compatibility with existing tests/clients
    app.include_router(
        auth.router, prefix="/api/auth", tags=["Authentication (legacy)"]
    )

    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

    app.include_router(quotes.router, prefix="/api/v1/quotes", tags=["Quotes"])

    app.include_router(service_quotes.router, prefix="/api/v1", tags=["Service Quotes"])

    app.include_router(simple_quotes.router, tags=["Simple Quotes"])

    app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice Processing"])

    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])

    # Enhanced monitoring endpoints
    @app.get("/api/v1/monitoring/metrics", tags=["Monitoring"])
    async def get_metrics():
        """Get application metrics."""
        ai_service = await get_ai_service()
        return await ai_service.get_health_status()

    # Health check endpoints
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Enhanced health check endpoint with AI service status."""
        db_healthy = check_db_health()

        try:
            ai_service = await get_ai_service()
            ai_health = await ai_service.get_health_status()
            ai_healthy = ai_health["service_status"] == "healthy"
        except Exception:
            ai_healthy = False

        overall_healthy = db_healthy and ai_healthy

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "version": settings.app_version,
            "timestamp": time.time(),
            "checks": {
                "database": db_healthy,
                "ai_service": ai_healthy,
                "overall": overall_healthy,
            },
        }

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


def setup_exception_handlers(app: FastAPI) -> None:
    """Set up exception handlers."""

    @app.exception_handler(QuoteMasterProException)
    async def quote_master_pro_exception_handler(
        request: Request, exc: QuoteMasterProException
    ):
        """Handle custom application exceptions."""
        logger.error(
            "Application error occurred",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            url=str(request.url),
            method=request.method,
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
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP error occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            url=str(request.url),
            method=request.method,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            },
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
            exc_info=True,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "An unexpected error occurred",
                    "debug": str(exc) if settings.debug else None,
                }
            },
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
        {
            "name": "Authentication",
            "description": "User authentication and authorization",
        },
        {"name": "Users", "description": "User management"},
        {"name": "Quotes", "description": "Quote generation and management"},
        {
            "name": "Service Quotes",
            "description": "Service quote calculation for window and pressure cleaning",
        },
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
