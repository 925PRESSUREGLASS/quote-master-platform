"""Quote management router for Quote Master Pro."""

from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from src.core.database import get_db
from src.api.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_optional_current_user,
    check_quote_quota
)
from src.api.models.user import User
from src.api.models.quote import (
    Quote,
    QuoteCategory,
    QuoteFavorite,
    QuoteCollection,
    QuoteCollectionItem,
    QuoteRating,
    QuoteStatus
)
from src.api.schemas.quote import (
    QuoteCreate,
    QuoteUpdate,
    QuoteResponse,
    QuotePublicResponse,
    QuoteGenerate,
    QuoteCategoryResponse,
    QuoteFavoriteResponse,
    QuoteFavoriteCreate,
    QuoteSearchRequest,
    QuoteSearchResponse,
    QuoteBulkAction,
    QuoteAnalytics,
    QuoteCollectionCreate,
    QuoteCollectionResponse,
    QuoteCollectionWithQuotes,
    QuoteRatingCreate,
    QuoteRatingResponse
)

router = APIRouter()


@router.post("/generate", response_model=QuoteResponse, dependencies=[Depends(check_quote_quota)])
async def generate_quote(
    quote_request: QuoteGenerate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Generate a new quote using AI."""
    
    # TODO: Implement AI quote generation
    # For now, create a placeholder quote
    
    # Get category if specified
    category_id = None
    if quote_request.category:
        category = db.query(QuoteCategory).filter(
            QuoteCategory.name.ilike(f"%{quote_request.category}%")
        ).first()
        if category:
            category_id = category.id
    
    # Create quote with placeholder text
    generated_text = f"Generated quote based on: {quote_request.prompt}"
    
    quote = Quote(
        user_id=current_user.id,
        category_id=category_id,
        text=generated_text,
        context=quote_request.context,
        source="ai_generated",
        ai_model=quote_request.ai_model or "gpt-4",
        prompt_used=quote_request.prompt,
        generation_params={
            "style": quote_request.style,
            "tone": quote_request.tone,
            "length": quote_request.length,
            "temperature": quote_request.temperature,
            "max_tokens": quote_request.max_tokens,
            "include_psychology": quote_request.include_psychology
        }
    )
    
    db.add(quote)
    
    # Update user stats
    current_user.increment_quote_count()
    current_user.api_calls_today += 1
    current_user.last_api_call_date = datetime.utcnow()
    
    db.commit()
    db.refresh(quote)
    
    # Background tasks for AI processing
    background_tasks.add_task(process_quote_ai_analysis, quote.id)
    
    return quote


@router.get("/", response_model=List[QuotePublicResponse])
async def list_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|popularity|likes|views)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """List public quotes."""
    
    query = db.query(Quote).filter(
        Quote.is_public == True,
        Quote.status == QuoteStatus.PUBLISHED,
        Quote.is_approved == True
    )
    
    # Apply filters
    if category_id:
        query = query.filter(Quote.category_id == category_id)
    
    if author:
        query = query.filter(Quote.author.ilike(f"%{author}%"))
    
    if search:
        query = query.filter(
            or_(
                Quote.text.ilike(f"%{search}%"),
                Quote.author.ilike(f"%{search}%"),
                Quote.context.ilike(f"%{search}%")
            )
        )
    
    # Apply sorting
    if sort_by == "popularity":
        order_column = Quote.popularity_score
    elif sort_by == "likes":
        order_column = Quote.like_count
    elif sort_by == "views":
        order_column = Quote.view_count
    else:
        order_column = Quote.created_at
    
    if sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())
    
    quotes = query.offset(skip).limit(limit).all()
    
    return quotes


@router.post("/search", response_model=QuoteSearchResponse)
async def search_quotes(
    search_request: QuoteSearchRequest,
    db: Session = Depends(get_db)
):
    """Advanced quote search."""
    
    query = db.query(Quote).filter(
        Quote.is_public == True,
        Quote.status == QuoteStatus.PUBLISHED,
        Quote.is_approved == True
    )
    
    # Apply search filters
    if search_request.query:
        query = query.filter(
            or_(
                Quote.text.ilike(f"%{search_request.query}%"),
                Quote.author.ilike(f"%{search_request.query}%"),
                Quote.context.ilike(f"%{search_request.query}%")
            )
        )
    
    if search_request.category_id:
        query = query.filter(Quote.category_id == search_request.category_id)
    
    if search_request.author:
        query = query.filter(Quote.author.ilike(f"%{search_request.author}%"))
    
    if search_request.tags:
        # TODO: Implement tag filtering with JSONB
        pass
    
    if search_request.min_length:
        query = query.filter(func.length(Quote.text) >= search_request.min_length)
    
    if search_request.max_length:
        query = query.filter(func.length(Quote.text) <= search_request.max_length)
    
    if search_request.sentiment:
        # Filter by sentiment score range
        sentiment_ranges = {
            "positive": (0.1, 1.0),
            "negative": (-1.0, -0.1),
            "neutral": (-0.1, 0.1)
        }
        if search_request.sentiment in sentiment_ranges:
            min_score, max_score = sentiment_ranges[search_request.sentiment]
            query = query.filter(
                and_(
                    Quote.sentiment_score >= min_score,
                    Quote.sentiment_score <= max_score
                )
            )
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting
    if search_request.sort_by and search_request.sort_order:
        sort_column = getattr(Quote, search_request.sort_by, Quote.created_at)
        if search_request.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # Apply pagination
    quotes = query.offset(search_request.offset).limit(search_request.limit).all()
    
    return QuoteSearchResponse(
        quotes=quotes,
        total=total,
        limit=search_request.limit,
        offset=search_request.offset,
        has_more=search_request.offset + len(quotes) < total
    )


@router.get("/{quote_id}", response_model=QuotePublicResponse)
async def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get a specific quote."""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check visibility
    if not quote.is_public and (not current_user or quote.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Increment view count
    quote.increment_view_count()
    db.commit()
    
    return quote


@router.get("/me/quotes", response_model=List[QuoteResponse])
async def get_my_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's quotes."""
    
    query = db.query(Quote).filter(Quote.user_id == current_user.id)
    
    if status:
        query = query.filter(Quote.status == status)
    
    quotes = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()
    
    return quotes


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Create a new quote manually."""
    
    quote = Quote(
        user_id=current_user.id,
        category_id=quote_data.category_id,
        text=quote_data.text,
        author=quote_data.author,
        context=quote_data.context,
        source="text_input",
        tags=quote_data.tags,
        is_public=quote_data.is_public
    )
    
    db.add(quote)
    current_user.increment_quote_count()
    db.commit()
    db.refresh(quote)
    
    return quote


@router.put("/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    quote_id: str,
    quote_update: QuoteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a quote."""
    
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.user_id == current_user.id
    ).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Update fields
    for field, value in quote_update.dict(exclude_unset=True).items():
        setattr(quote, field, value)
    
    quote.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(quote)
    
    return quote


@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a quote."""
    
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.user_id == current_user.id
    ).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Soft delete
    quote.status = QuoteStatus.DELETED
    db.commit()
    
    return {"message": "Quote deleted successfully"}


# Categories
@router.get("/categories/", response_model=List[QuoteCategoryResponse])
async def list_categories(
    db: Session = Depends(get_db)
):
    """List all quote categories."""
    
    categories = db.query(QuoteCategory).filter(
        QuoteCategory.is_active == True
    ).order_by(QuoteCategory.sort_order, QuoteCategory.name).all()
    
    return categories


# Favorites
@router.post("/favorites", response_model=QuoteFavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: QuoteFavoriteCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Add quote to favorites."""
    
    # Check if quote exists
    quote = db.query(Quote).filter(Quote.id == favorite_data.quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check if already favorited
    existing_favorite = db.query(QuoteFavorite).filter(
        QuoteFavorite.user_id == current_user.id,
        QuoteFavorite.quote_id == favorite_data.quote_id
    ).first()
    
    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Quote already in favorites"
        )
    
    favorite = QuoteFavorite(
        user_id=current_user.id,
        quote_id=favorite_data.quote_id,
        notes=favorite_data.notes
    )
    
    db.add(favorite)
    
    # Update quote favorite count
    quote.favorite_count += 1
    
    db.commit()
    db.refresh(favorite)
    
    return favorite


@router.delete("/favorites/{quote_id}")
async def remove_favorite(
    quote_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Remove quote from favorites."""
    
    favorite = db.query(QuoteFavorite).filter(
        QuoteFavorite.user_id == current_user.id,
        QuoteFavorite.quote_id == quote_id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    # Update quote favorite count
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if quote and quote.favorite_count > 0:
        quote.favorite_count -= 1
    
    db.delete(favorite)
    db.commit()
    
    return {"message": "Quote removed from favorites"}


@router.get("/me/favorites", response_model=List[QuoteFavoriteResponse])
async def get_my_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's favorite quotes."""
    
    favorites = db.query(QuoteFavorite).filter(
        QuoteFavorite.user_id == current_user.id
    ).order_by(QuoteFavorite.created_at.desc()).offset(skip).limit(limit).all()
    
    return favorites


# Quote actions
@router.post("/{quote_id}/like")
async def like_quote(
    quote_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Like a quote."""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # TODO: Implement like tracking to prevent double-likes
    quote.increment_like_count()
    db.commit()
    
    return {"message": "Quote liked successfully", "likes": quote.like_count}


@router.post("/{quote_id}/share")
async def share_quote(
    quote_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Track quote share."""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    quote.increment_share_count()
    db.commit()
    
    return {"message": "Quote share tracked", "shares": quote.share_count}


async def process_quote_ai_analysis(quote_id: str):
    """Background task to process AI analysis for quote."""
    # TODO: Implement AI analysis
    # - Sentiment analysis
    # - Emotional tone detection
    # - Psychological profiling
    # - Quality scoring
    pass