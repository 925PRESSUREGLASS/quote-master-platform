"""
Quote model for Quote Master Pro
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any

from src.config.database import Base

class QuoteCategory(PyEnum):
    MOTIVATIONAL = "motivational"
    INSPIRATIONAL = "inspirational"
    WISDOM = "wisdom"
    LOVE = "love"
    SUCCESS = "success"
    LIFE = "life"
    HAPPINESS = "happiness"
    FRIENDSHIP = "friendship"
    CUSTOM = "custom"

class AIModel(PyEnum):
    GPT4 = "gpt-4"
    GPT3_5 = "gpt-3.5-turbo"
    CLAUDE = "claude-3-sonnet"
    CLAUDE_HAIKU = "claude-3-haiku"

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author = Column(String(255))
    category = Column(Enum(QuoteCategory), default=QuoteCategory.INSPIRATIONAL)
    ai_model = Column(Enum(AIModel))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    voice_recording_id = Column(Integer, ForeignKey("voice_recordings.id"), nullable=True)
    
    # AI Analysis
    sentiment_score = Column(Float)  # -1 to 1
    emotion_primary = Column(String(50))
    emotion_confidence = Column(Float)
    psychology_profile = Column(Text)  # JSON stored as text
    
    # Metadata
    prompt_used = Column(Text)
    generation_context = Column(Text)  # JSON stored as text
    is_favorite = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="quotes")
    voice_recording = relationship("VoiceRecording", back_populates="quotes")

    def __repr__(self):
        return f"<Quote(id={self.id}, author='{self.author}', category='{self.category}')>"

    @property
    def short_content(self) -> str:
        """Get shortened version of quote content"""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."

    @property
    def word_count(self) -> int:
        """Get word count of quote"""
        return len(self.content.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert quote to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "author": self.author,
            "category": self.category.value if self.category else None,
            "ai_model": self.ai_model.value if self.ai_model else None,
            "user_id": self.user_id,
            "voice_recording_id": self.voice_recording_id,
            "sentiment_score": self.sentiment_score,
            "emotion_primary": self.emotion_primary,
            "emotion_confidence": self.emotion_confidence,
            "psychology_profile": self.psychology_profile,
            "is_favorite": self.is_favorite,
            "is_public": self.is_public,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_public_dict(self) -> Dict[str, Any]:
        """Convert quote to public dictionary (safe for sharing)"""
        return {
            "id": self.id,
            "content": self.content,
            "author": self.author,
            "category": self.category.value if self.category else None,
            "sentiment_score": self.sentiment_score,
            "emotion_primary": self.emotion_primary,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }