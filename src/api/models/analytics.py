"""Analytics and tracking model definitions."""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.core.database import Base


class EventType(str, Enum):
    """Analytics event types."""
    # User events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    USER_PROFILE_UPDATE = "user_profile_update"
    
    # Quote events
    QUOTE_GENERATED = "quote_generated"
    QUOTE_VIEWED = "quote_viewed"
    QUOTE_LIKED = "quote_liked"
    QUOTE_SHARED = "quote_shared"
    QUOTE_FAVORITED = "quote_favorited"
    QUOTE_COPIED = "quote_copied"
    QUOTE_DOWNLOADED = "quote_downloaded"
    
    # Voice events
    VOICE_RECORDING_STARTED = "voice_recording_started"
    VOICE_RECORDING_COMPLETED = "voice_recording_completed"
    VOICE_PROCESSING_STARTED = "voice_processing_started"
    VOICE_PROCESSING_COMPLETED = "voice_processing_completed"
    
    # AI events
    AI_REQUEST_SENT = "ai_request_sent"
    AI_RESPONSE_RECEIVED = "ai_response_received"
    AI_ERROR_OCCURRED = "ai_error_occurred"
    
    # Page/Feature events
    PAGE_VIEW = "page_view"
    FEATURE_USED = "feature_used"
    SEARCH_PERFORMED = "search_performed"
    FILTER_APPLIED = "filter_applied"
    
    # Engagement events
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    TIME_SPENT = "time_spent"
    
    # Error events
    ERROR_OCCURRED = "error_occurred"
    API_ERROR = "api_error"
    
    # Business events
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_COMPLETED = "payment_completed"


class AnalyticsEvent(Base):
    """Analytics event tracking."""
    
    __tablename__ = "analytics_events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key (optional for anonymous events)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Event information
    event_type = Column(String(50), nullable=False)
    event_name = Column(String(255), nullable=False)
    event_category = Column(String(100), nullable=True)
    
    # Event data
    properties = Column(JSON, nullable=True)  # Event-specific properties
    value = Column(Float, nullable=True)  # Numeric value for the event
    
    # Context information
    page_url = Column(String(500), nullable=True)
    page_title = Column(String(255), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Technical information
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 compatible
    device_type = Column(String(50), nullable=True)  # mobile, tablet, desktop
    browser = Column(String(100), nullable=True)
    operating_system = Column(String(100), nullable=True)
    screen_resolution = Column(String(20), nullable=True)
    
    # Geographic information
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Performance data
    page_load_time = Column(Float, nullable=True)  # milliseconds
    api_response_time = Column(Float, nullable=True)  # milliseconds
    
    # A/B testing
    experiment_id = Column(String(100), nullable=True)
    variant = Column(String(50), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    server_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="analytics_events")
    session = relationship("UserSession", back_populates="events")
    
    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"


class UserSession(Base):
    """User session tracking."""
    
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key (optional for anonymous sessions)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Session identification
    session_token = Column(String(255), unique=True, nullable=False)
    anonymous_id = Column(String(255), nullable=True)  # For anonymous users
    
    # Session metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    
    # Entry/exit information
    landing_page = Column(String(500), nullable=True)
    exit_page = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    
    # Technical information
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 compatible
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    operating_system = Column(String(100), nullable=True)
    
    # Geographic information
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Session metrics
    page_views = Column(Integer, default=0)
    quotes_generated = Column(Integer, default=0)
    voice_recordings = Column(Integer, default=0)
    interactions = Column(Integer, default=0)
    
    # Quality metrics
    bounce = Column(Boolean, default=False)  # Single page session
    engaged = Column(Boolean, default=False)  # Meaningful interaction
    converted = Column(Boolean, default=False)  # Achieved goal
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    events = relationship("AnalyticsEvent", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, started_at={self.started_at})>"
    
    def calculate_duration(self) -> Optional[int]:
        """Calculate session duration in seconds."""
        if self.ended_at and self.started_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds())
        return None
    
    def end_session(self) -> None:
        """End the session and calculate metrics."""
        self.ended_at = datetime.utcnow()
        self.duration_seconds = self.calculate_duration()
        self.is_active = False
        
        # Determine if session was a bounce
        self.bounce = self.page_views <= 1 and (self.duration_seconds or 0) < 30
        
        # Determine if session was engaged
        self.engaged = (
            self.page_views > 2 or
            (self.duration_seconds or 0) > 120 or
            self.quotes_generated > 0 or
            self.voice_recordings > 0
        )


class PageView(Base):
    """Page view tracking."""
    
    __tablename__ = "page_views"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Page information
    url = Column(String(500), nullable=False)
    title = Column(String(255), nullable=True)
    path = Column(String(255), nullable=False)
    query_params = Column(JSON, nullable=True)
    
    # Navigation
    referrer = Column(String(500), nullable=True)
    previous_page = Column(String(500), nullable=True)
    
    # Timing
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_on_page = Column(Float, nullable=True)  # seconds
    load_time = Column(Float, nullable=True)  # milliseconds
    
    # Engagement
    scroll_depth = Column(Float, nullable=True)  # percentage 0-100
    clicks = Column(Integer, default=0)
    interactions = Column(Integer, default=0)
    
    def __repr__(self) -> str:
        return f"<PageView(id={self.id}, path={self.path}, user_id={self.user_id})>"


class ConversionEvent(Base):
    """Conversion tracking."""
    
    __tablename__ = "conversion_events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Conversion information
    goal_name = Column(String(255), nullable=False)
    goal_category = Column(String(100), nullable=True)
    value = Column(Float, nullable=True)  # Monetary or point value
    
    # Attribution
    first_touch_source = Column(String(100), nullable=True)
    last_touch_source = Column(String(100), nullable=True)
    conversion_path = Column(JSON, nullable=True)  # Array of touchpoints
    
    # Timing
    converted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_to_conversion = Column(Integer, nullable=True)  # seconds from first touch
    
    # Context
    properties = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ConversionEvent(id={self.id}, goal_name={self.goal_name}, user_id={self.user_id})>"


class FunnelStep(Base):
    """Funnel step tracking."""
    
    __tablename__ = "funnel_steps"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Funnel information
    funnel_name = Column(String(255), nullable=False)
    step_name = Column(String(255), nullable=False)
    step_order = Column(Integer, nullable=False)
    
    # Completion
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    time_spent = Column(Float, nullable=True)  # seconds on this step
    
    # Context
    properties = Column(JSON, nullable=True)
    
    def __repr__(self) -> str:
        return f"<FunnelStep(funnel_name={self.funnel_name}, step_name={self.step_name})>"


class ABTestVariant(Base):
    """A/B test variant assignment."""
    
    __tablename__ = "ab_test_variants"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Test information
    experiment_id = Column(String(100), nullable=False)
    variant = Column(String(50), nullable=False)
    
    # Assignment
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Anonymous identifier for non-logged users
    anonymous_id = Column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<ABTestVariant(experiment_id={self.experiment_id}, variant={self.variant})>"