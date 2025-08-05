"""User management router for Quote Master Pro."""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.core.database import get_db
from src.api.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_optional_current_user
)
from src.api.models.user import User, UserProfile, APIKey
from src.api.models.quote import Quote
from src.api.models.voice import VoiceRecording
from src.api.schemas.user import (
    UserUpdate,
    UserResponse,
    UserPublicResponse,
    UserProfile as UserProfileSchema,
    UserPreferences,
    UserStats,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithSecret,
)
from src.core.security import generate_api_key, hash_api_key

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    
    # Check if username is already taken (if being updated)
    if user_update.username and user_update.username != current_user.username:
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
    
    # Update user fields
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.delete("/me")
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current user's account."""
    
    # Soft delete - mark as deleted instead of actually deleting
    from src.api.models.user import UserStatus
    current_user.status = UserStatus.DELETED
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Account has been deleted successfully"}


@router.get("/me/stats", response_model=UserStats)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's statistics."""
    
    # Calculate statistics
    total_quotes = db.query(Quote).filter(Quote.user_id == current_user.id).count()
    total_favorites = current_user.favorites.count() if current_user.favorites else 0
    total_voice_recordings = db.query(VoiceRecording).filter(
        VoiceRecording.user_id == current_user.id
    ).count()
    
    # Quotes this month
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    quotes_this_month = db.query(Quote).filter(
        Quote.user_id == current_user.id,
        Quote.created_at >= start_of_month
    ).count()
    
    # Calculate days since joining
    days_active = (datetime.utcnow() - current_user.created_at).days
    
    # Average quotes per day
    avg_quotes_per_day = total_quotes / max(days_active, 1)
    
    # Most used category (simplified)
    most_used_category = None  # TODO: Implement category analysis
    
    return UserStats(
        total_quotes=total_quotes,
        total_favorites=total_favorites,
        total_voice_recordings=total_voice_recordings,
        quotes_this_month=quotes_this_month,
        average_quotes_per_day=round(avg_quotes_per_day, 2),
        most_used_category=most_used_category,
        join_date=current_user.created_at,
        days_active=days_active
    )


@router.get("/me/preferences", response_model=UserPreferences)
async def get_my_preferences(
    current_user: User = Depends(get_current_user)
):
    """Get current user's preferences."""
    
    # Parse preferences from JSON string
    import json
    preferences = {}
    if current_user.preferences:
        try:
            preferences = json.loads(current_user.preferences)
        except json.JSONDecodeError:
            pass
    
    return UserPreferences(**preferences)


@router.put("/me/preferences", response_model=UserPreferences)
async def update_my_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's preferences."""
    
    import json
    current_user.preferences = json.dumps(preferences.dict())
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    
    return preferences


@router.get("/{user_id}", response_model=UserPublicResponse)
async def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get public user profile."""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/", response_model=List[UserPublicResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List public user profiles."""
    
    query = db.query(User).filter(User.is_active == True)
    
    if search:
        query = query.filter(
            func.or_(
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    users = query.offset(skip).limit(limit).all()
    
    return users


# API Key management
@router.get("/me/api-keys", response_model=List[APIKeyResponse])
async def list_my_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List current user's API keys."""
    
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()
    
    return api_keys


@router.post("/me/api-keys", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new API key."""
    
    # Check if user already has too many API keys
    existing_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.is_active == True
    ).count()
    
    if existing_keys >= 10:  # Limit to 10 active API keys
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum number of API keys reached"
        )
    
    # Generate API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = api_key[:8]
    
    # Set expiry if provided
    expires_at = None
    if api_key_data.expires_days:
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_days)
    
    # Create API key record
    db_api_key = APIKey(
        user_id=current_user.id,
        name=api_key_data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=api_key_data.scopes,
        expires_at=expires_at
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    # Return response with the actual API key (only shown once)
    response = APIKeyWithSecret.from_orm(db_api_key)
    response.api_key = api_key
    
    return response


@router.delete("/me/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an API key."""
    
    api_key = db.query(APIKey).filter(
        APIKey.id == api_key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Soft delete
    api_key.is_active = False
    db.commit()
    
    return {"message": "API key deleted successfully"}


# Admin endpoints
@router.get("/admin/users", response_model=List[UserResponse])
async def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: List all users."""
    
    query = db.query(User)
    
    if search:
        query = query.filter(
            func.or_(
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status:
        query = query.filter(User.status == status)
    
    users = query.offset(skip).limit(limit).all()
    
    return users


@router.put("/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    user_update: dict,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Update user account."""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update allowed fields
    allowed_fields = ['role', 'status', 'is_active', 'is_verified', 'subscription_tier']
    
    for field, value in user_update.items():
        if field in allowed_fields:
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user