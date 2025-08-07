"""
Quote model for Quote Master Pro
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from typing import Optional, Dict, Any
import re

from src.config.database import Base

class QuoteCategory(PyEnum):
    """Categories for organizing quotes"""
    MOTIVATIONAL = "motivational"
    INSPIRATIONAL = "inspirational"
    WISDOM = "wisdom"
    LOVE = "love"
    SUCCESS = "success"
    LIFE = "life"
    HAPPINESS = "happiness"
    FRIENDSHIP = "friendship"
    LEADERSHIP = "leadership"
    CREATIVITY = "creativity"
    SPIRITUAL = "spiritual"
    HUMOR = "humor"
    CUSTOM = "custom"

class QuoteSource(PyEnum):
    """Source of the quote"""
    AI_GENERATED = "ai_generated"
    USER_INPUT = "user_input"
    VOICE_TO_TEXT = "voice_to_text"
    IMPORTED = "imported"

class AIModel(PyEnum):
    """AI models used for quote generation"""
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    GPT3_5 = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    GEMINI_PRO = "gemini-pro"

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author = Column(String(255))
    category = Column(Enum(QuoteCategory), default=QuoteCategory.INSPIRATIONAL)
    source = Column(Enum(QuoteSource), default=QuoteSource.AI_GENERATED)
    ai_model = Column(Enum(AIModel))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    voice_recording_id = Column(Integer, ForeignKey("voice_recordings.id"), nullable=True)
    
    # Content Analysis
    sentiment_score = Column(Float)  # -1 to 1 (negative to positive)
    emotion_primary = Column(String(50))
    emotion_confidence = Column(Float)  # 0 to 1
    psychology_profile = Column(Text)  # JSON stored as text
    themes = Column(Text)  # JSON array of themes
    keywords = Column(Text)  # JSON array of keywords
    
    # Generation Context
    prompt_used = Column(Text)
    generation_context = Column(Text)  # JSON stored as text
    generation_temperature = Column(Float)  # AI generation temperature
    
    # User Interaction
    is_favorite = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # Quality Metrics
    quality_score = Column(Float)  # 0 to 1 overall quality rating
    readability_score = Column(Float)  # 0 to 1 readability rating
    originality_score = Column(Float)  # 0 to 1 uniqueness rating
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="quotes")
    voice_recording = relationship("VoiceRecording", back_populates="quotes")

    def __repr__(self):
        return f"<Quote(id={self.id}, author='{getattr(self, 'author', 'Unknown')}')>"

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

    def short_content(self, max_length=100):
        """Get shortened version of quote content"""
        try:
            content = getattr(self, 'content', '')
            if len(content) <= max_length:
                return content
            return content[:max_length-3] + "..."
        except:
            return ""

    def word_count(self):
        """Get word count of quote"""
        try:
            content = getattr(self, 'content', '')
            return len(content.split()) if content else 0
        except:
            return 0

    def character_count(self):
        """Get character count of quote"""
        try:
            content = getattr(self, 'content', '')
            return len(content) if content else 0
        except:
            return 0

    def reading_time_seconds(self, wpm=200):
        """Estimate reading time in seconds"""
        try:
            words = self.word_count()
            return int((words / wpm) * 60) if words > 0 else 0
        except:
            return 0

    def has_author(self):
        """Check if quote has an author"""
        try:
            author = getattr(self, 'author', None)
            return bool(author and author.strip())
        except:
            return False

    def is_high_quality(self, threshold=0.7):
        """Check if quote is considered high quality"""
        try:
            quality = getattr(self, 'quality_score', 0)
            return quality >= threshold if quality is not None else False
        except:
            return False

    def is_trending(self):
        """Check if quote has recent engagement"""
        try:
            views = getattr(self, 'view_count', 0)
            shares = getattr(self, 'share_count', 0)
            likes = getattr(self, 'like_count', 0)
            return (views + shares + likes) > 10  # Simple trending logic
        except:
            return False

    def engagement_score(self):
        """Calculate engagement score based on interactions"""
        try:
            views = getattr(self, 'view_count', 0)
            shares = getattr(self, 'share_count', 0)
            likes = getattr(self, 'like_count', 0)
            # Weight different interactions
            return (views * 1) + (shares * 3) + (likes * 2)
        except:
            return 0

    def to_dict(self, include_analytics=False):
        """Convert quote to dictionary"""
        try:
            data = {
                "id": getattr(self, 'id', None),
                "content": getattr(self, 'content', ''),
                "author": getattr(self, 'author', None),
                "category": self._safe_enum_value('category'),
                "source": self._safe_enum_value('source'),
                "ai_model": self._safe_enum_value('ai_model'),
                "user_id": getattr(self, 'user_id', None),
                "voice_recording_id": getattr(self, 'voice_recording_id', None),
                "sentiment_score": getattr(self, 'sentiment_score', None),
                "emotion_primary": getattr(self, 'emotion_primary', None),
                "emotion_confidence": getattr(self, 'emotion_confidence', None),
                "psychology_profile": getattr(self, 'psychology_profile', None),
                "themes": getattr(self, 'themes', None),
                "keywords": getattr(self, 'keywords', None),
                "is_favorite": getattr(self, 'is_favorite', False),
                "is_public": getattr(self, 'is_public', False),
                "is_featured": getattr(self, 'is_featured', False),
                "quality_score": getattr(self, 'quality_score', None),
                "readability_score": getattr(self, 'readability_score', None),
                "originality_score": getattr(self, 'originality_score', None),
                "word_count": self.word_count(),
                "character_count": self.character_count(),
                "reading_time_seconds": self.reading_time_seconds(),
                "has_author": self.has_author(),
                "created_at": self._safe_isoformat('created_at'),
                "updated_at": self._safe_isoformat('updated_at'),
                "last_accessed": self._safe_isoformat('last_accessed')
            }
            
            if include_analytics:
                data.update({
                    "view_count": getattr(self, 'view_count', 0),
                    "share_count": getattr(self, 'share_count', 0),
                    "like_count": getattr(self, 'like_count', 0),
                    "engagement_score": self.engagement_score(),
                    "is_trending": self.is_trending(),
                    "is_high_quality": self.is_high_quality()
                })
            
            return data
        except Exception as e:
            return {
                "id": getattr(self, 'id', None),
                "content": getattr(self, 'content', 'Error loading quote'),
                "error": str(e)
            }

    def to_public_dict(self):
        """Convert quote to public dictionary (safe for sharing)"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "content": getattr(self, 'content', ''),
                "author": getattr(self, 'author', None),
                "category": self._safe_enum_value('category'),
                "sentiment_score": getattr(self, 'sentiment_score', None),
                "emotion_primary": getattr(self, 'emotion_primary', None),
                "themes": getattr(self, 'themes', None),
                "word_count": self.word_count(),
                "reading_time_seconds": self.reading_time_seconds(),
                "created_at": self._safe_isoformat('created_at'),
                "is_featured": getattr(self, 'is_featured', False)
            }
        except:
            return {
                "id": getattr(self, 'id', None),
                "content": getattr(self, 'content', 'Error loading quote')
            }

    def to_summary_dict(self):
        """Convert quote to summary dictionary for lists"""
        try:
            return {
                "id": getattr(self, 'id', None),
                "content": self.short_content(150),
                "author": getattr(self, 'author', None),
                "category": self._safe_enum_value('category'),
                "is_favorite": getattr(self, 'is_favorite', False),
                "is_public": getattr(self, 'is_public', False),
                "word_count": self.word_count(),
                "sentiment_score": getattr(self, 'sentiment_score', None),
                "created_at": self._safe_isoformat('created_at')
            }
        except:
            return {
                "id": getattr(self, 'id', None),
                "content": "Error loading quote"
            }


class QuoteGeneration(Base):
    """Model for tracking quote generation requests and results."""
    __tablename__ = "quote_generations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    prompt = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    category = Column(Enum(QuoteCategory), nullable=True)
    ai_model = Column(Enum(AIModel), nullable=False)
    generated_content = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=True)
    processing_time = Column(Float, nullable=True)
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="quote_generations")
    
    def __repr__(self):
        return f"<QuoteGeneration(id={self.id}, user_id={self.user_id}, success={self.success})>"