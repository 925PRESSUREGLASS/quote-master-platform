"""
Analytics model for Quote Master Pro
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum as PyEnum

from src.config.database import Base

class EventType(PyEnum):
    """Types of analytics events"""
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    PERFORMANCE = "performance"
    ERROR = "error"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"

class EventCategory(PyEnum):
    """Categories of events for better organization"""
    AUTH = "auth"
    QUOTE = "quote"
    VOICE = "voice"
    PROFILE = "profile"
    NAVIGATION = "navigation"
    SEARCH = "search"
    SHARING = "sharing"
    AI_INTERACTION = "ai_interaction"

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Event Classification
    event_type = Column(Enum(EventType), nullable=False, index=True)
    event_category = Column(Enum(EventCategory), nullable=False, index=True)
    event_name = Column(String(100), nullable=False)
    event_action = Column(String(50))  # click, view, create, delete, etc.
    event_label = Column(String(100))  # additional context
    event_value = Column(Float)  # numeric value associated with event
    event_data = Column(Text)  # JSON stored as text for additional metadata
    
    # Session Information
    session_id = Column(String(100), index=True)
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    referrer = Column(String(500))
    
    # Location & Device
    country_code = Column(String(2))
    device_type = Column(String(20))  # desktop, mobile, tablet
    browser = Column(String(50))
    os = Column(String(50))
    
    # Performance Metrics
    duration = Column(Float)  # seconds
    page_load_time = Column(Float)  # seconds
    response_time = Column(Float)  # API response time in ms
    
    # Engagement Metrics
    scroll_depth = Column(Float)  # percentage of page scrolled
    time_on_page = Column(Float)  # seconds spent on page
    clicks_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="analytics_events")

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, event_type='{self.event_type}', event_name='{self.event_name}')>"

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

    def is_user_event(self):
        """Check if this is a user-generated event"""
        try:
            return getattr(self, 'user_id', None) is not None
        except:
            return False

    def is_error_event(self):
        """Check if this is an error event"""
        try:
            event_type = getattr(self, 'event_type', None)
            return event_type == EventType.ERROR
        except:
            return False

    def is_conversion_event(self):
        """Check if this is a conversion event"""
        try:
            event_type = getattr(self, 'event_type', None)
            return event_type == EventType.CONVERSION
        except:
            return False

    def has_high_engagement(self):
        """Check if event indicates high user engagement"""
        try:
            time_on_page = getattr(self, 'time_on_page', 0) or 0
            scroll_depth = getattr(self, 'scroll_depth', 0) or 0
            clicks = getattr(self, 'clicks_count', 0) or 0
            
            return (time_on_page > 30 or  # More than 30 seconds
                   scroll_depth > 0.5 or  # Scrolled more than 50%
                   clicks > 3)  # More than 3 clicks
        except:
            return False

    def get_performance_score(self):
        """Calculate performance score based on load times"""
        try:
            load_time = getattr(self, 'page_load_time', None)
            response_time = getattr(self, 'response_time', None)
            
            if not load_time and not response_time:
                return None
            
            # Performance scoring (lower is better)
            score = 1.0
            if load_time:
                if load_time > 3.0:
                    score -= 0.3
                elif load_time > 1.5:
                    score -= 0.1
            
            if response_time:
                if response_time > 1000:  # 1 second
                    score -= 0.3
                elif response_time > 500:  # 500ms
                    score -= 0.1
            
            return max(0.0, score)
        except:
            return None

    def to_dict(self, include_sensitive=False):
        """Convert analytics event to dictionary"""
        try:
            data = {
                "id": getattr(self, 'id', None),
                "user_id": getattr(self, 'user_id', None),
                "event_type": self._safe_enum_value('event_type'),
                "event_category": self._safe_enum_value('event_category'),
                "event_name": getattr(self, 'event_name', None),
                "event_action": getattr(self, 'event_action', None),
                "event_label": getattr(self, 'event_label', None),
                "event_value": getattr(self, 'event_value', None),
                "event_data": getattr(self, 'event_data', None),
                "session_id": getattr(self, 'session_id', None),
                "device_type": getattr(self, 'device_type', None),
                "browser": getattr(self, 'browser', None),
                "os": getattr(self, 'os', None),
                "country_code": getattr(self, 'country_code', None),
                "duration": getattr(self, 'duration', None),
                "page_load_time": getattr(self, 'page_load_time', None),
                "response_time": getattr(self, 'response_time', None),
                "scroll_depth": getattr(self, 'scroll_depth', None),
                "time_on_page": getattr(self, 'time_on_page', None),
                "clicks_count": getattr(self, 'clicks_count', 0),
                "created_at": self._safe_isoformat('created_at'),
                "is_user_event": self.is_user_event(),
                "is_error_event": self.is_error_event(),
                "has_high_engagement": self.has_high_engagement(),
                "performance_score": self.get_performance_score()
            }
            
            if include_sensitive:
                data.update({
                    "user_agent": getattr(self, 'user_agent', None),
                    "ip_address": getattr(self, 'ip_address', None),
                    "referrer": getattr(self, 'referrer', None)
                })
            
            return data
        except Exception as e:
            return {
                "id": getattr(self, 'id', None),
                "event_name": getattr(self, 'event_name', 'unknown'),
                "error": str(e)
            }

    def to_summary_dict(self):
        """Convert analytics event to summary dictionary for lists"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "event_type": self._safe_enum_value('event_type'),
                "event_category": self._safe_enum_value('event_category'),
                "event_name": getattr(self, 'event_name', None),
                "event_action": getattr(self, 'event_action', None),
                "user_id": getattr(self, 'user_id', None),
                "duration": getattr(self, 'duration', None),
                "created_at": self._safe_isoformat('created_at'),
                "is_error_event": self.is_error_event(),
                "has_high_engagement": self.has_high_engagement()
            }
        except:
            return {
                "id": getattr(self, 'id', None),
                "event_name": getattr(self, 'event_name', 'unknown')
            }

    def to_metrics_dict(self):
        """Convert to metrics-focused dictionary for dashboard"""
        try:
            return {
                "event_type": self._safe_enum_value('event_type'),
                "event_category": self._safe_enum_value('event_category'),
                "event_name": getattr(self, 'event_name', None),
                "event_value": getattr(self, 'event_value', None),
                "duration": getattr(self, 'duration', None),
                "page_load_time": getattr(self, 'page_load_time', None),
                "time_on_page": getattr(self, 'time_on_page', None),
                "scroll_depth": getattr(self, 'scroll_depth', None),
                "clicks_count": getattr(self, 'clicks_count', 0),
                "device_type": getattr(self, 'device_type', None),
                "country_code": getattr(self, 'country_code', None),
                "created_at": self._safe_isoformat('created_at'),
                "performance_score": self.get_performance_score()
            }
        except:
            return {
                "event_name": getattr(self, 'event_name', 'unknown'),
                "created_at": self._safe_isoformat('created_at')
            }