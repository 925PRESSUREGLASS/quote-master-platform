"""Quote-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator
from uuid import UUID

from src.api.models.quote import QuoteSource, QuoteStatus


class QuoteBase(BaseModel):
    """Base quote schema."""
    text: str = Field(..., min_length=1, max_length=5000)
    author: Optional[str] = Field(None, max_length=255)
    context: Optional[str] = Field(None, max_length=1000)


class QuoteCreate(QuoteBase):
    """Quote creation schema."""
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = []
    is_public: bool = True


class QuoteUpdate(BaseModel):
    """Quote update schema."""
    text: Optional[str] = Field(None, min_length=1, max_length=5000)
    author: Optional[str] = Field(None, max_length=255)
    context: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None


class QuoteGenerate(BaseModel):
    """Quote generation schema."""
    prompt: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = None
    style: Optional[str] = None
    length: Optional[str] = Field(None, pattern="^(short|medium|long)$")
    tone: Optional[str] = None
    author_style: Optional[str] = None
    context: Optional[str] = None
    ai_model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=10, le=1000)
    include_psychology: bool = True
    
    @validator('style')
    def validate_style(cls, v):
        if v and v not in ['inspirational', 'motivational', 'philosophical', 
                          'humorous', 'poetic', 'spiritual', 'business', 'life']:
            raise ValueError('Invalid style')
        return v
    
    @validator('tone')
    def validate_tone(cls, v):
        if v and v not in ['positive', 'negative', 'neutral', 'optimistic', 
                          'pessimistic', 'serious', 'playful', 'formal', 'casual']:
            raise ValueError('Invalid tone')
        return v


class QuoteResponse(QuoteBase):
    """Quote response schema."""
    id: UUID
    user_id: UUID
    category_id: Optional[UUID]
    source: QuoteSource
    ai_model: Optional[str]
    psychological_profile: Optional[Dict[str, Any]]
    emotional_tone: Optional[str]
    sentiment_score: Optional[float]
    complexity_score: Optional[float]
    quality_score: Optional[float]
    popularity_score: float
    view_count: int
    like_count: int
    share_count: int
    favorite_count: int
    is_approved: bool
    is_featured: bool
    is_public: bool
    status: QuoteStatus
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    word_count: int
    character_count: int
    is_long_quote: bool
    
    class Config:
        from_attributes = True


class QuotePublicResponse(BaseModel):
    """Public quote response schema (without sensitive data)."""
    id: UUID
    text: str
    author: Optional[str]
    context: Optional[str]
    emotional_tone: Optional[str]
    sentiment_score: Optional[float]
    popularity_score: float
    view_count: int
    like_count: int
    share_count: int
    favorite_count: int
    tags: Optional[List[str]]
    created_at: datetime
    word_count: int
    character_count: int
    
    class Config:
        from_attributes = True


class QuoteCategoryBase(BaseModel):
    """Base quote category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class QuoteCategoryCreate(QuoteCategoryBase):
    """Quote category creation schema."""
    parent_id: Optional[UUID] = None
    sort_order: int = 0


class QuoteCategoryUpdate(BaseModel):
    """Quote category update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class QuoteCategoryResponse(QuoteCategoryBase):
    """Quote category response schema."""
    id: UUID
    slug: str
    parent_id: Optional[UUID]
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class QuoteFavoriteResponse(BaseModel):
    """Quote favorite response schema."""
    id: UUID
    user_id: UUID
    quote_id: UUID
    notes: Optional[str]
    created_at: datetime
    quote: QuoteResponse
    
    class Config:
        from_attributes = True


class QuoteFavoriteCreate(BaseModel):
    """Quote favorite creation schema."""
    quote_id: UUID
    notes: Optional[str] = None


class QuoteSearchRequest(BaseModel):
    """Quote search request schema."""
    query: Optional[str] = None
    category_id: Optional[UUID] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    sentiment: Optional[str] = None
    sort_by: Optional[str] = Field(None, pattern="^(created_at|popularity|likes|views)$")
    sort_order: Optional[str] = Field(None, pattern="^(asc|desc)$")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class QuoteSearchResponse(BaseModel):
    """Quote search response schema."""
    quotes: List[QuotePublicResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class QuoteBulkAction(BaseModel):
    """Quote bulk action schema."""
    quote_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    action: str = Field(..., pattern="^(delete|archive|publish|feature)$")


class QuoteAnalytics(BaseModel):
    """Quote analytics schema."""
    quote_id: UUID
    views_today: int
    views_this_week: int
    views_this_month: int
    likes_today: int
    likes_this_week: int
    likes_this_month: int
    shares_today: int
    shares_this_week: int
    shares_this_month: int
    engagement_rate: float
    trending_score: float


class QuoteCollectionBase(BaseModel):
    """Base quote collection schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = False


class QuoteCollectionCreate(QuoteCollectionBase):
    """Quote collection creation schema."""
    quote_ids: Optional[List[UUID]] = []


class QuoteCollectionUpdate(BaseModel):
    """Quote collection update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None
    cover_image_url: Optional[str] = None


class QuoteCollectionResponse(QuoteCollectionBase):
    """Quote collection response schema."""
    id: UUID
    user_id: UUID
    cover_image_url: Optional[str]
    is_featured: bool
    created_at: datetime
    updated_at: Optional[datetime]
    quote_count: int
    
    class Config:
        from_attributes = True


class QuoteCollectionWithQuotes(QuoteCollectionResponse):
    """Quote collection with quotes schema."""
    quotes: List[QuotePublicResponse]


class QuoteRatingCreate(BaseModel):
    """Quote rating creation schema."""
    quote_id: UUID
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = Field(None, max_length=1000)


class QuoteRatingResponse(BaseModel):
    """Quote rating response schema."""
    id: UUID
    user_id: UUID
    quote_id: UUID
    rating: int
    review: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True