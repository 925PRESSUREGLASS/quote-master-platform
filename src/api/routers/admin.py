"""Admin router for Quote Master Pro."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from src.core.database import get_db
from src.api.dependencies import get_current_admin_user
from src.api.models.user import User, UserRole, UserStatus
from src.api.models.quote import Quote, QuoteCategory, QuoteStatus
from src.api.models.voice import VoiceRecording, VoiceProcessingJob
from src.api.models.analytics import AnalyticsEvent, UserSession
from src.api.schemas.user import UserResponse
from src.api.schemas.quote import QuoteCategoryCreate, QuoteCategoryUpdate, QuoteCategoryResponse

router = APIRouter()


# System Overview
@router.get("/overview")
async def get_system_overview(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system overview statistics."""
    
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    premium_users = db.query(User).filter(User.role.in_([UserRole.PREMIUM, UserRole.MODERATOR, UserRole.ADMIN])).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    # New users in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_30d = db.query(User).filter(User.created_at >= thirty_days_ago).count()
    
    # Quote statistics
    total_quotes = db.query(Quote).count()
    published_quotes = db.query(Quote).filter(Quote.status == QuoteStatus.PUBLISHED).count()
    quotes_today = db.query(Quote).filter(
        Quote.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    quotes_30d = db.query(Quote).filter(Quote.created_at >= thirty_days_ago).count()
    
    # Voice statistics
    total_recordings = db.query(VoiceRecording).count()
    recordings_30d = db.query(VoiceRecording).filter(VoiceRecording.created_at >= thirty_days_ago).count()
    
    # Processing jobs
    pending_jobs = db.query(VoiceProcessingJob).filter(
        VoiceProcessingJob.status.in_(["pending", "started", "processing"])
    ).count()
    
    failed_jobs = db.query(VoiceProcessingJob).filter(
        VoiceProcessingJob.status == "failed"
    ).count()
    
    # System health
    db_healthy = True  # TODO: Implement actual health check
    redis_healthy = True  # TODO: Implement Redis health check
    ai_services_healthy = True  # TODO: Implement AI services health check
    
    return {
        "timestamp": datetime.utcnow(),
        "users": {
            "total": total_users,
            "active": active_users,
            "premium": premium_users,
            "verified": verified_users,
            "new_30d": new_users_30d,
        },
        "quotes": {
            "total": total_quotes,
            "published": published_quotes,
            "today": quotes_today,
            "new_30d": quotes_30d,
        },
        "voice": {
            "total_recordings": total_recordings,
            "new_30d": recordings_30d,
            "pending_jobs": pending_jobs,
            "failed_jobs": failed_jobs,
        },
        "system_health": {
            "database": db_healthy,
            "redis": redis_healthy,
            "ai_services": ai_services_healthy,
            "overall": db_healthy and redis_healthy and ai_services_healthy,
        }
    }


# User Management
@router.get("/users", response_model=List[UserResponse])
async def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    is_verified: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|last_login_at|email|username)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List and filter users."""
    
    query = db.query(User)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if status:
        query = query.filter(User.status == status)
    
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Apply sorting
    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    users = query.offset(skip).limit(limit).all()
    
    return users


@router.put("/users/{user_id}")
async def admin_update_user(
    user_id: str,
    updates: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user account (admin only)."""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Define allowed fields for admin updates
    allowed_fields = {
        'role', 'status', 'is_active', 'is_verified', 
        'subscription_tier', 'subscription_expires_at'
    }
    
    # Apply updates
    for field, value in updates.items():
        if field in allowed_fields and hasattr(user, field):
            setattr(user, field, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    permanent: bool = Query(False),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete or deactivate user account."""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    if permanent:
        # Permanent deletion (use with caution)
        db.delete(user)
        message = "User permanently deleted"
    else:
        # Soft deletion
        user.status = UserStatus.DELETED
        user.is_active = False
        user.updated_at = datetime.utcnow()
        message = "User account deactivated"
    
    db.commit()
    
    return {"message": message}


# Quote Management
@router.get("/quotes")
async def admin_list_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[QuoteStatus] = Query(None),
    is_approved: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List and filter quotes."""
    
    query = db.query(Quote)
    
    # Apply filters
    if status:
        query = query.filter(Quote.status == status)
    
    if is_approved is not None:
        query = query.filter(Quote.is_approved == is_approved)
    
    if is_featured is not None:
        query = query.filter(Quote.is_featured == is_featured)
    
    if search:
        query = query.filter(
            or_(
                Quote.text.ilike(f"%{search}%"),
                Quote.author.ilike(f"%{search}%"),
                Quote.context.ilike(f"%{search}%")
            )
        )
    
    if user_id:
        query = query.filter(Quote.user_id == user_id)
    
    # Apply sorting
    sort_column = getattr(Quote, sort_by, Quote.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    quotes = query.offset(skip).limit(limit).all()
    
    return quotes


@router.put("/quotes/{quote_id}/moderate")
async def moderate_quote(
    quote_id: str,
    action: str = Query(..., pattern="^(approve|reject|feature|unfeature)$"),
    notes: Optional[str] = None,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Moderate a quote."""
    
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )
    
    if action == "approve":
        quote.is_approved = True
        quote.status = QuoteStatus.PUBLISHED
        message = "Quote approved"
    elif action == "reject":
        quote.is_approved = False
        quote.status = QuoteStatus.ARCHIVED
        message = "Quote rejected"
    elif action == "feature":
        quote.is_featured = True
        quote.featured_at = datetime.utcnow()
        message = "Quote featured"
    elif action == "unfeature":
        quote.is_featured = False
        quote.featured_at = None
        message = "Quote unfeatured"
    
    if notes:
        quote.moderation_notes = notes
    
    quote.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": message, "quote_id": quote_id}


# Category Management
@router.get("/categories", response_model=List[QuoteCategoryResponse])
async def admin_list_categories(
    include_inactive: bool = Query(False),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List quote categories."""
    
    query = db.query(QuoteCategory)
    
    if not include_inactive:
        query = query.filter(QuoteCategory.is_active == True)
    
    categories = query.order_by(QuoteCategory.sort_order, QuoteCategory.name).all()
    
    return categories


@router.post("/categories", response_model=QuoteCategoryResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_category(
    category_data: QuoteCategoryCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new quote category."""
    
    # Generate slug from name
    import re
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', category_data.name.lower()).strip('-')
    
    # Check if slug already exists
    existing_category = db.query(QuoteCategory).filter(QuoteCategory.slug == slug).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category with this name already exists"
        )
    
    category = QuoteCategory(
        name=category_data.name,
        slug=slug,
        description=category_data.description,
        color=category_data.color,
        icon=category_data.icon,
        parent_id=category_data.parent_id,
        sort_order=category_data.sort_order
    )
    
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


@router.put("/categories/{category_id}", response_model=QuoteCategoryResponse)
async def admin_update_category(
    category_id: str,
    category_update: QuoteCategoryUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update a quote category."""
    
    category = db.query(QuoteCategory).filter(QuoteCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update fields
    for field, value in category_update.dict(exclude_unset=True).items():
        if field == "name" and value:
            # Update slug when name changes
            import re
            new_slug = re.sub(r'[^a-zA-Z0-9]+', '-', value.lower()).strip('-')
            
            # Check if new slug conflicts
            existing = db.query(QuoteCategory).filter(
                QuoteCategory.slug == new_slug,
                QuoteCategory.id != category_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Category name conflicts with existing category"
                )
            
            category.slug = new_slug
        
        setattr(category, field, value)
    
    category.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(category)
    
    return category


@router.delete("/categories/{category_id}")
async def admin_delete_category(
    category_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a quote category."""
    
    category = db.query(QuoteCategory).filter(QuoteCategory.id == category_id).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category has quotes
    quote_count = db.query(Quote).filter(Quote.category_id == category_id).count()
    
    if quote_count > 0:
        # Soft delete if has quotes
        category.is_active = False
        message = f"Category deactivated ({quote_count} quotes remain)"
    else:
        # Hard delete if no quotes
        db.delete(category)
        message = "Category deleted"
    
    db.commit()
    
    return {"message": message}


# System Maintenance
@router.post("/maintenance/cleanup")
async def run_cleanup(
    background_tasks: BackgroundTasks,
    cleanup_type: str = Query(..., pattern="^(temp_files|old_sessions|failed_jobs|deleted_users)$"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Run system cleanup tasks."""
    
    background_tasks.add_task(execute_cleanup_task, cleanup_type)
    
    return {"message": f"Cleanup task '{cleanup_type}' started"}


@router.get("/maintenance/jobs")
async def list_background_jobs(
    job_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List background processing jobs."""
    
    query = db.query(VoiceProcessingJob)
    
    if job_type:
        query = query.filter(VoiceProcessingJob.job_type == job_type)
    
    if status:
        query = query.filter(VoiceProcessingJob.status == status)
    
    jobs = query.order_by(desc(VoiceProcessingJob.created_at)).limit(100).all()
    
    return jobs


@router.post("/maintenance/retry-failed-jobs")
async def retry_failed_jobs(
    background_tasks: BackgroundTasks,
    job_type: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Retry failed processing jobs."""
    
    query = db.query(VoiceProcessingJob).filter(
        VoiceProcessingJob.status == "failed",
        VoiceProcessingJob.retry_count < VoiceProcessingJob.max_retries
    )
    
    if job_type:
        query = query.filter(VoiceProcessingJob.job_type == job_type)
    
    failed_jobs = query.all()
    
    for job in failed_jobs:
        background_tasks.add_task(retry_processing_job, job.id)
    
    return {"message": f"Retrying {len(failed_jobs)} failed jobs"}


# Reports
@router.get("/reports/user-activity")
async def get_user_activity_report(
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Generate user activity report."""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Daily active users
    daily_active = db.query(
        func.date(AnalyticsEvent.timestamp).label('date'),
        func.count(func.distinct(AnalyticsEvent.user_id)).label('active_users')
    ).filter(
        AnalyticsEvent.timestamp >= start_date,
        AnalyticsEvent.user_id.isnot(None)
    ).group_by(func.date(AnalyticsEvent.timestamp)).all()
    
    # User retention
    # TODO: Implement retention calculation
    
    return {
        "period": f"{days} days",
        "start_date": start_date,
        "end_date": end_date,
        "daily_active_users": [
            {"date": str(day.date), "active_users": day.active_users}
            for day in daily_active
        ],
        "retention_cohorts": []  # TODO: Implement
    }


# Background task functions
async def execute_cleanup_task(cleanup_type: str):
    """Execute system cleanup task."""
    # TODO: Implement cleanup tasks
    pass


async def retry_processing_job(job_id: str):
    """Retry a failed processing job."""
    # TODO: Implement job retry logic
    pass