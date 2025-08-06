"""Quote-related model definitions."""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.core.database import Base


class QuoteStatus(str, Enum):
    """Quote status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class QuoteSource(str, Enum):
    """Quote source enumeration."""
    AI_GENERATED = "ai_generated"
    VOICE_INPUT = "voice_input"
    TEXT_INPUT = "text_input"
    CURATED = "curated"
    IMPORTED = "imported"


class QuoteCategory(Base):
    """Quote category model."""
    
    __tablename__ = "quote_categories"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Category information
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)
    
    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("quote_categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("QuoteCategory", remote_side=[id], backref="children")
    quotes = relationship("Quote", back_populates="category")
    
    def __repr__(self) -> str:
        return f"<QuoteCategory(id={self.id}, name={self.name})>"


class Quote(Base):
    """Quote model."""
    
    __tablename__ = "quotes"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("quote_categories.id"), nullable=True)
    
    # Quote content
    text = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    context = Column(Text, nullable=True)  # Context or situation for the quote
    
    # Generation metadata
    source = Column(String(20), default=QuoteSource.AI_GENERATED)
    ai_model = Column(String(50), nullable=True)  # Which AI model generated it
    prompt_used = Column(Text, nullable=True)  # Original prompt
    generation_params = Column(JSON, nullable=True)  # AI generation parameters
    
    # Psychology analysis
    psychological_profile = Column(JSON, nullable=True)  # Psychological insights
    emotional_tone = Column(String(50), nullable=True)
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    complexity_score = Column(Float, nullable=True)  # 0 to 1
    
    # Voice-related (if generated from voice)
    voice_recording_id = Column(UUID(as_uuid=True), ForeignKey("voice_recordings.id"), nullable=True)
    original_audio_duration = Column(Float, nullable=True)  # seconds
    transcription_confidence = Column(Float, nullable=True)  # 0 to 1
    
    # Quality and engagement
    quality_score = Column(Float, nullable=True)  # 0 to 1
    popularity_score = Column(Float, default=0.0)  # Calculated from engagement
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    
    # Content moderation
    is_approved = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    moderation_notes = Column(Text, nullable=True)
    
    # Status and lifecycle
    status = Column(String(20), default=QuoteStatus.PUBLISHED)
    
    # SEO and discovery
    tags = Column(JSON, nullable=True)  # Array of tags
    keywords = Column(Text, nullable=True)  # Comma-separated keywords
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    featured_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="quotes")
    category = relationship("QuoteCategory", back_populates="quotes")
    voice_recording = relationship("VoiceRecording", backref="quotes")
    favorites = relationship("QuoteFavorite", back_populates="quote", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"<Quote(id={self.id}, text='{preview}')>"
    
    def increment_view_count(self) -> None:
        """Increment view count."""
        self.view_count += 1
    
    def increment_like_count(self) -> None:
        """Increment like count."""
        self.like_count += 1
    
    def increment_share_count(self) -> None:
        """Increment share count."""
        self.share_count += 1
    
    def calculate_popularity_score(self) -> float:
        """Calculate popularity score based on engagement metrics."""
        # Simple algorithm: weighted sum of engagement metrics
        score = (
            self.view_count * 0.1 +
            self.like_count * 2.0 +
            self.share_count * 5.0 +
            self.favorite_count * 3.0
        )
        
        # Time decay factor (newer quotes get slight boost)
        days_old = (datetime.utcnow() - self.created_at).days
        time_factor = max(0.1, 1.0 - (days_old * 0.01))
        
        return score * time_factor
    
    @property
    def word_count(self) -> int:
        """Get word count of the quote."""
        return len(self.text.split())
    
    @property
    def character_count(self) -> int:
        """Get character count of the quote."""
        return len(self.text)
    
    @property
    def is_long_quote(self) -> bool:
        """Check if quote is considered long."""
        return self.word_count > 50 or self.character_count > 280


class QuoteFavorite(Base):
    """User's favorite quotes."""
    
    __tablename__ = "quote_favorites"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    
    # Metadata
    notes = Column(Text, nullable=True)  # Personal notes about the quote
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    quote = relationship("Quote", back_populates="favorites")
    
    def __repr__(self) -> str:
        return f"<QuoteFavorite(user_id={self.user_id}, quote_id={self.quote_id})>"


class QuoteCollection(Base):
    """User-created collections of quotes."""
    
    __tablename__ = "quote_collections"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Collection information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    
    # Privacy and sharing
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<QuoteCollection(id={self.id}, name={self.name})>"


class QuoteCollectionItem(Base):
    """Items in a quote collection."""
    
    __tablename__ = "quote_collection_items"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    collection_id = Column(UUID(as_uuid=True), ForeignKey("quote_collections.id"), nullable=False)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    
    # Ordering
    sort_order = Column(Integer, default=0)
    
    # Metadata
    notes = Column(Text, nullable=True)
    
    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<QuoteCollectionItem(collection_id={self.collection_id}, quote_id={self.quote_id})>"


class QuoteRating(Base):
    """User ratings for quotes."""
    
    __tablename__ = "quote_ratings"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    
    # Rating (1-5 stars)
    rating = Column(Integer, nullable=False)  # 1-5
    review = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<QuoteRating(user_id={self.user_id}, quote_id={self.quote_id}, rating={self.rating})>"