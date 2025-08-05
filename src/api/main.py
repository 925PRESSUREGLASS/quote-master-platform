"""Main FastAPI application for Quote Master Pro."""

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
from src.api.routers import (
    auth,
    quotes,
    voice,
    analytics,
    users,
    admin
)

# Configure structured logging
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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Quote Master Pro API", version=settings.app_version)
    
    try:
        # Initialize database
        if not check_db_health():
            raise Exception("Database connection failed")
        
        # Initialize database tables
        init_db()
        logger.info("Database initialized successfully")
        
        # Additional startup tasks
        await startup_tasks()
        
        logger.info("Application startup completed")
        
    except Exception as e:
        logger.error("Application startup failed", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Quote Master Pro API")
    await shutdown_tasks()
    logger.info("Application shutdown completed")


async def startup_tasks():
    """Perform startup tasks."""
    # Initialize Redis connection
    # Initialize AI service connections
    # Load ML models if needed
    # Set up monitoring
    pass


async def shutdown_tasks():
    """Perform shutdown tasks."""
    # Close database connections
    # Close Redis connections
    # Clean up resources
    pass


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered quote generation platform with voice recognition and psychological insights",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add routes
    setup_routes(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Set up application middleware."""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )
    
    # Trusted host middleware (security)
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.quotemasterpro.com", "quotemasterpro.com"]
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
                process_time=round(process_time, 4)
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
    """Set up application routes."""
    
    # API routes
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
    
    # Health check endpoints
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        db_healthy = check_db_health()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "version": settings.app_version,
            "timestamp": time.time(),
            "checks": {
                "database": db_healthy,
                # Add more health checks here
            }
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