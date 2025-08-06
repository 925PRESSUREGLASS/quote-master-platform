"""API routers for Quote Master Pro."""
from .auth import router as auth_router
from .users import router as users_router
from .quotes import router as quotes_router
from .service_quotes import router as service_quotes_router
from .voice import router as voice_router
from .analytics import router as analytics_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "users_router", 
    "quotes_router",
    "service_quotes_router",
    "voice_router",
    "analytics_router",
    "admin_router"
]