"""Pydantic schemas for API serialization."""

from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    LoginRequest,
    LoginResponse,
    TokenResponse,
)

from .quote import (
    QuoteCreate,
    QuoteUpdate,
    QuoteResponse,
    QuoteGenerate,
    QuoteCategoryResponse,
    QuoteFavoriteResponse,
)

from .voice import (
    VoiceRecordingResponse,
    VoiceProcessingJobResponse,
    VoiceProcessRequest,
)

from .analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    UserSessionResponse,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserUpdate", 
    "UserResponse",
    "UserProfile",
    "LoginRequest",
    "LoginResponse",
    "TokenResponse",
    
    # Quote schemas
    "QuoteCreate",
    "QuoteUpdate",
    "QuoteResponse", 
    "QuoteGenerate",
    "QuoteCategoryResponse",
    "QuoteFavoriteResponse",
    
    # Voice schemas
    "VoiceRecordingResponse",
    "VoiceProcessingJobResponse",
    "VoiceProcessRequest",
    
    # Analytics schemas
    "AnalyticsEventCreate",
    "AnalyticsEventResponse",
    "UserSessionResponse",
]