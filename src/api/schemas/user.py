"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID

from src.api.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                'Password must contain at least one uppercase letter, '
                'one lowercase letter, one digit, and one special character'
            )
        
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfile(BaseModel):
    """User profile schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    occupation: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    twitter_handle: Optional[str] = None
    linkedin_url: Optional[str] = None
    instagram_handle: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    role: UserRole
    status: UserStatus
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_login_at: Optional[datetime]
    subscription_tier: str
    total_quotes_generated: int
    total_voice_requests: int
    display_name: str
    
    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    """Public user response schema (limited information)."""
    id: UUID
    username: Optional[str]
    full_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    total_quotes_generated: int
    created_at: datetime
    display_name: str
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Email verification confirmation schema."""
    token: str


class UserPreferences(BaseModel):
    """User preferences schema."""
    theme: str = "light"
    notifications_enabled: bool = True
    email_notifications: bool = True
    quote_style_preference: Optional[str] = None
    default_quote_category: Optional[str] = None
    voice_model_preference: Optional[str] = None
    ai_model_preference: Optional[str] = None


class UserStats(BaseModel):
    """User statistics schema."""
    total_quotes: int
    total_favorites: int
    total_voice_recordings: int
    quotes_this_month: int
    average_quotes_per_day: float
    most_used_category: Optional[str]
    join_date: datetime
    days_active: int


class APIKeyCreate(BaseModel):
    """API key creation schema."""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: Optional[List[str]] = None
    expires_days: Optional[int] = Field(None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """API key response schema."""
    id: UUID
    name: str
    key_prefix: str
    scopes: Optional[List[str]]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    usage_count: int
    rate_limit: int
    
    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """API key response with secret (only shown once)."""
    api_key: str