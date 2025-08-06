"""
Analytics model for Quote Master Pro
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum as PyEnum

from src.config.database import Base

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Event Information
    event_type = Column(String(50), nullable=False, index=True)
    event_name = Column(String(100), nullable=False)
    event_data = Column(Text)  # JSON stored as text
    
    # Session Information
    session_id = Column(String(100), index=True)
    user_agent = Column(String(500))
    ip_address = Column(String(45))
    
    # Performance Metrics
    duration = Column(Float)  # seconds
    page_load_time = Column(Float)  # seconds
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="analytics_events")

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, event_type='{self.event_type}', event_name='{self.event_name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert analytics event to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "event_name": self.event_name,
            "event_data": self.event_data,
            "session_id": self.session_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "duration": self.duration,
            "page_load_time": self.page_load_time,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }