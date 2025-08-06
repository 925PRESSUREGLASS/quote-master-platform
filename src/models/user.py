"""
User model for Quote Master Pro
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any

from src.config.database import Base

class UserRole(PyEnum):
    """User roles in the system"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class UserStatus(PyEnum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(Enum(UserRole), default=UserRole.USER)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_email_confirmed = Column(Boolean, default=False)
    avatar_url = Column(String(500))
    bio = Column(Text)
    preferences = Column(Text)  # JSON stored as text
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")  # ISO language code
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    email_confirmed_at = Column(DateTime(timezone=True))

    # Relationships
    quotes = relationship("Quote", back_populates="user", cascade="all, delete-orphan")  # Legacy
    service_quotes = relationship("ServiceQuote", back_populates="user", cascade="all, delete-orphan")
    voice_recordings = relationship("VoiceRecording", back_populates="user", cascade="all, delete-orphan")
    analytics_events = relationship("AnalyticsEvent", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def _safe_isoformat(self, attr_name):
        """Safely get isoformat from datetime attribute"""
        try:
            dt = getattr(self, attr_name, None)
            return dt.isoformat() if dt is not None else None
        except:
            return None

    def _safe_enum_value(self, attr_name, default=None):
        """Safely get value from enum attribute"""
        try:
            enum_val = getattr(self, attr_name, None)
            return enum_val.value if enum_val is not None else default
        except:
            return default

    def full_name(self):
        """Get user's full name"""
        try:
            first = getattr(self, 'first_name', None)
            last = getattr(self, 'last_name', None)
            
            if first and last:
                return f"{first} {last}"
            elif first:
                return first
            elif last:
                return last
            return getattr(self, 'username', 'Unknown User')
        except:
            return 'Unknown User'

    def is_admin(self):
        """Check if user is admin"""
        try:
            role = getattr(self, 'role', None)
            return role == UserRole.ADMIN
        except:
            return False

    def is_moderator(self):
        """Check if user is moderator"""
        try:
            role = getattr(self, 'role', None)
            return role == UserRole.MODERATOR
        except:
            return False

    def is_staff(self):
        """Check if user is admin or moderator"""
        return self.is_admin() or self.is_moderator()

    def is_account_active(self):
        """Check if account is active (both is_active and status)"""
        try:
            active = getattr(self, 'is_active', False)
            status = getattr(self, 'status', None)
            return active and status == UserStatus.ACTIVE
        except:
            return False

    def can_login(self):
        """Check if user can login"""
        try:
            return (self.is_account_active() and 
                   getattr(self, 'is_verified', False))
        except:
            return False

    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary (safe for API responses)"""
        try:
            data = {
                "id": getattr(self, 'id', None),
                "email": getattr(self, 'email', None),
                "username": getattr(self, 'username', None),
                "first_name": getattr(self, 'first_name', None),
                "last_name": getattr(self, 'last_name', None),
                "full_name": self.full_name(),
                "role": self._safe_enum_value('role'),
                "status": self._safe_enum_value('status'),
                "is_active": getattr(self, 'is_active', False),
                "is_verified": getattr(self, 'is_verified', False),
                "is_email_confirmed": getattr(self, 'is_email_confirmed', False),
                "avatar_url": getattr(self, 'avatar_url', None),
                "bio": getattr(self, 'bio', None),
                "timezone": getattr(self, 'timezone', 'UTC'),
                "language": getattr(self, 'language', 'en'),
                "created_at": self._safe_isoformat('created_at'),
                "updated_at": self._safe_isoformat('updated_at'),
                "last_login": self._safe_isoformat('last_login'),
                "email_confirmed_at": self._safe_isoformat('email_confirmed_at'),
                "is_admin": self.is_admin(),
                "is_moderator": self.is_moderator(),
                "is_staff": self.is_staff(),
                "can_login": self.can_login()
            }
            
            if include_sensitive:
                data["preferences"] = getattr(self, 'preferences', None)
            
            return data
        except Exception as e:
            return {
                "id": getattr(self, 'id', None),
                "username": getattr(self, 'username', 'unknown'),
                "error": str(e)
            }

    def to_public_dict(self):
        """Convert user to public dictionary (no sensitive info)"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "username": getattr(self, 'username', None),
                "full_name": self.full_name(),
                "avatar_url": getattr(self, 'avatar_url', None),
                "bio": getattr(self, 'bio', None),
                "role": self._safe_enum_value('role'),
                "created_at": self._safe_isoformat('created_at'),
                "is_verified": getattr(self, 'is_verified', False)
            }
        except:
            return {
                "id": getattr(self, 'id', None),
                "username": getattr(self, 'username', 'unknown')
            }

    def to_summary_dict(self):
        """Convert user to summary dictionary for lists"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "username": getattr(self, 'username', None),
                "full_name": self.full_name(),
                "email": getattr(self, 'email', None),
                "role": self._safe_enum_value('role'),
                "status": self._safe_enum_value('status'),
                "is_active": getattr(self, 'is_active', False),
                "last_login": self._safe_isoformat('last_login'),
                "created_at": self._safe_isoformat('created_at')
            }
        except:
            return {
                "id": getattr(self, 'id', None),
                "username": getattr(self, 'username', 'unknown')
            }