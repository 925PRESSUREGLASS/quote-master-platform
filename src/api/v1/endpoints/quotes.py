"""
Quote endpoints for Quote Master Pro
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.config.database import get_db_session
from src.services.auth import AuthService
from src.services.ai.openai_service import OpenAIService, QuoteRequest
from src.models.user import User
from src.models.quote import Quote, QuoteCategory, AIModel

router = APIRouter()

class QuoteCreateRequest(BaseModel):
    prompt: str
    category: QuoteCategory = QuoteCategory.INSPIRATIONAL
    tone: Optional[str] = None
    length: str = "medium"
    ai_model: AIModel = AIModel.GPT4

class QuoteResponse(BaseModel):
    id: int
    content: str
    author: Optional[str]
    category: str
    ai_model: Optional[str]
    sentiment_score: Optional[float]
    emotion_primary: Optional[str]
    is_favorite: bool
    is_public: bool
    created_at: str

class QuoteListResponse(BaseModel):
    quotes: List[QuoteResponse]
    total: int
    page: int
    per_page: int

@router.post("/generate", response_model=QuoteResponse)
async def generate_quote(
    request: QuoteCreateRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db_session)
):
    """Generate a new quote using AI"""
    try:
        # Use OpenAI service to generate quote
        ai_service = OpenAIService()
        
        quote_request = QuoteRequest(
            prompt=request.prompt,
            category=request.category.value,
            tone=request.tone,
            length=request.length,
            model=request.ai_model.value
        )
        
        ai_response = await ai_service.generate_quote(quote_request)
        
        # Analyze sentiment
        sentiment_analysis = await ai_service.analyze_sentiment(ai_response.content)
        
        # Save to database
        quote = Quote(
            content=ai_response.content,
            author=ai_response.author,
            category=request.category,
            ai_model=request.ai_model,
            user_id=current_user.id,
            prompt_used=request.prompt,
            sentiment_score=sentiment_analysis.get("score"),
            emotion_primary=sentiment_analysis.get("primary_emotion"),
            emotion_confidence=sentiment_analysis.get("confidence")
        )
        
        db.add(quote)
        db.commit()
        db.refresh(quote)
        
        return QuoteResponse(
            id=quote.id,
            content=quote.content,
            author=quote.author,
            category=quote.category.value,
            ai_model=quote.ai_model.value if quote.ai_model else None,
            sentiment_score=quote.sentiment_score,
            emotion_primary=quote.emotion_primary,
            is_favorite=quote.is_favorite,
            is_public=quote.is_public,
            created_at=quote.created_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quote generation failed: {str(e)}"
        )

@router.get("/my-quotes", response_model=QuoteListResponse)
async def get_my_quotes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[QuoteCategory] = None,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get current user's quotes"""
    query = db.query(Quote).filter(Quote.user_id == current_user.id)
    
    if category:
        query = query.filter(Quote.category == category)
    
    total = query.count()
    quotes = query.offset((page - 1) * per_page).limit(per_page).all()
    
    quote_responses = [
        QuoteResponse(
            id=quote.id,
            content=quote.content,
            author=quote.author,
            category=quote.category.value,
            ai_model=quote.ai_model.value if quote.ai_model else None,
            sentiment_score=quote.sentiment_score,
            emotion_primary=quote.emotion_primary,
            is_favorite=quote.is_favorite,
            is_public=quote.is_public,
            created_at=quote.created_at.isoformat()
        )
        for quote in quotes
    ]
    
    return QuoteListResponse(
        quotes=quote_responses,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/public", response_model=QuoteListResponse)
async def get_public_quotes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[QuoteCategory] = None,
    db: Session = Depends(get_db_session)
):
    """Get public quotes"""
    query = db.query(Quote).filter(Quote.is_public == True)
    
    if category:
        query = query.filter(Quote.category == category)
    
    total = query.count()
    quotes = query.offset((page - 1) * per_page).limit(per_page).all()
    
    quote_responses = [
        QuoteResponse(
            id=quote.id,
            content=quote.content,
            author=quote.author,
            category=quote.category.value,
            ai_model=quote.ai_model.value if quote.ai_model else None,
            sentiment_score=quote.sentiment_score,
            emotion_primary=quote.emotion_primary,
            is_favorite=False,  # Don't show favorite status for public quotes
            is_public=quote.is_public,
            created_at=quote.created_at.isoformat()
        )
        for quote in quotes
    ]
    
    return QuoteListResponse(
        quotes=quote_responses,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get a specific quote"""
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    # Check permissions
    if quote.user_id != current_user.id and not quote.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return QuoteResponse(
        id=quote.id,
        content=quote.content,
        author=quote.author,
        category=quote.category.value,
        ai_model=quote.ai_model.value if quote.ai_model else None,
        sentiment_score=quote.sentiment_score,
        emotion_primary=quote.emotion_primary,
        is_favorite=quote.is_favorite,
        is_public=quote.is_public,
        created_at=quote.created_at.isoformat()
    )

@router.put("/{quote_id}/favorite")
async def toggle_favorite(
    quote_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db_session)
):
    """Toggle quote favorite status"""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.user_id == current_user.id
    ).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    quote.is_favorite = not quote.is_favorite
    db.commit()
    
    return {"is_favorite": quote.is_favorite}

@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: int,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db_session)
):
    """Delete a quote"""
    quote = db.query(Quote).filter(
        Quote.id == quote_id,
        Quote.user_id == current_user.id
    ).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    db.delete(quote)
    db.commit()
    
    return {"message": "Quote deleted successfully"}