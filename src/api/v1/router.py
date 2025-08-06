"""
Main API v1 router for Quote Master Pro
"""

from fastapi import APIRouter
from src.api.v1.endpoints import auth, quotes, voice, analytics, admin, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["authentication"]
)

api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["users"]
)

api_router.include_router(
    quotes.router, 
    prefix="/quotes", 
    tags=["quotes"]
)

api_router.include_router(
    voice.router, 
    prefix="/voice", 
    tags=["voice"]
)

api_router.include_router(
    analytics.router, 
    prefix="/analytics", 
    tags=["analytics"]
)

api_router.include_router(
    admin.router, 
    prefix="/admin", 
    tags=["admin"]
)