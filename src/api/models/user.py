"""User model definitions."""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.core.database import Base


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    PREMIUM = "premium"
    MODERATOR = "moderator"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Account status
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    
    # Subscription information
    subscription_tier = Column(String(50), default="free")
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    total_quotes_generated = Column(Integer, default=0)
    total_voice_requests = Column(Integer, default=0)
    api_calls_today = Column(Integer, default=0)
    last_api_call_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    quotes = relationship("Quote", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("QuoteFavorite", back_populates="user", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    voice_recordings = relationship("VoiceRecording", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium access."""
        return self.role in [UserRole.PREMIUM, UserRole.MODERATOR, UserRole.ADMIN]
    
    @property
    def display_name(self) -> str:
        """Get display name (full name or username)."""
        return self.full_name or self.username or self.email.split("@")[0]
    
    def can_generate_quotes(self) -> bool:
        """Check if user can generate quotes."""
        return self.is_active and self.status == UserStatus.ACTIVE
    
    def increment_quote_count(self) -> None:
        """Increment total quotes generated."""
        self.total_quotes_generated += 1
    
    def increment_voice_count(self) -> None:
        """Increment total voice requests."""
        self.total_voice_requests += 1


class UserProfile(Base):
    """Extended user profile information."""
    
    __tablename__ = "user_profiles"
    
    # Primary key and foreign key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    
    # Personal information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    
    # Location
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Professional information
    occupation = Column(String(200), nullable=True)
    company = Column(String(200), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Social media
    twitter_handle = Column(String(100), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    instagram_handle = Column(String(100), nullable=True)
    
    # Interests and preferences
    favorite_topics = Column(Text, nullable=True)  # JSON array
    quote_style_preference = Column(String(50), nullable=True)
    personality_type = Column(String(20), nullable=True)  # MBTI, etc.
    
    # Privacy settings
    profile_visibility = Column(String(20), default="public")  # public, private, friends
    show_activity = Column(Boolean, default=True)
    allow_contact = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id})>"


class APIKey(Base):
    """API key model for programmatic access."""
    
    __tablename__ = "api_keys"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Key information
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    
    # Permissions and limitations
    scopes = Column(Text, nullable=True)  # JSON array of allowed scopes
    rate_limit = Column(Integer, default=1000)  # Requests per day
    usage_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, user_id={self.user_id}, name={self.name})>"
    
    def is_valid(self) -> bool:
        """Check if API key is valid and active."""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def increment_usage(self) -> None:
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()