"""Analytics router for Quote Master Pro."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from src.core.database import get_db
from src.api.dependencies import (
    get_current_user,
    get_current_admin_user,
    get_optional_current_user,
    get_user_session
)
from src.api.models.user import User
from src.api.models.analytics import (
    AnalyticsEvent,
    UserSession,
    PageView,
    ConversionEvent,
    FunnelStep,
    EventType
)
from src.api.models.quote import Quote
from src.api.models.voice import VoiceRecording
from src.api.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    UserSessionResponse,
    PageViewCreate,
    PageViewResponse,
    ConversionEventCreate,
    ConversionEventResponse,
    AnalyticsQuery,
    AnalyticsReport,
    UserEngagementMetrics,
    QuoteGenerationMetrics,
    VoiceProcessingMetrics,
    RealtimeMetrics,
    DashboardData,
    FunnelAnalysis,
    ABTestResult
)

router = APIRouter()


@router.post("/events", response_model=AnalyticsEventResponse, status_code=status.HTTP_201_CREATED)
async def track_event(
    event_data: AnalyticsEventCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    session: Optional[UserSession] = Depends(get_user_session)
):
    """Track an analytics event."""
    
    # Extract request information
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    # Create event
    event = AnalyticsEvent(
        user_id=current_user.id if current_user else None,
        session_id=session.id if session else None,
        event_type=event_data.event_type,
        event_name=event_data.event_name,
        event_category=event_data.event_category,
        properties=event_data.properties,
        value=event_data.value,
        page_url=event_data.page_url,
        page_title=event_data.page_title,
        referrer=event_data.referrer,
        user_agent=user_agent,
        ip_address=ip_address,
        device_type=event_data.device_type,
        browser=event_data.browser,
        operating_system=event_data.operating_system,
        screen_resolution=event_data.screen_resolution,
        country=event_data.country,
        region=event_data.region,
        city=event_data.city,
        timezone=event_data.timezone,
        page_load_time=event_data.page_load_time,
        api_response_time=event_data.api_response_time,
        experiment_id=event_data.experiment_id,
        variant=event_data.variant
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return event


@router.post("/page-views", response_model=PageViewResponse, status_code=status.HTTP_201_CREATED)
async def track_page_view(
    page_view_data: PageViewCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    session: Optional[UserSession] = Depends(get_user_session)
):
    """Track a page view."""
    
    page_view = PageView(
        user_id=current_user.id if current_user else None,
        session_id=session.id if session else None,
        url=page_view_data.url,
        title=page_view_data.title,
        path=page_view_data.path,
        query_params=page_view_data.query_params,
        referrer=page_view_data.referrer,
        previous_page=page_view_data.previous_page,
        time_on_page=page_view_data.time_on_page,
        load_time=page_view_data.load_time,
        scroll_depth=page_view_data.scroll_depth,
        clicks=page_view_data.clicks,
        interactions=page_view_data.interactions
    )
    
    db.add(page_view)
    
    # Update session page view count
    if session:
        session.page_views += 1
        session.last_activity_at = datetime.utcnow()
    
    db.commit()
    db.refresh(page_view)
    
    return page_view


@router.post("/conversions", response_model=ConversionEventResponse, status_code=status.HTTP_201_CREATED)
async def track_conversion(
    conversion_data: ConversionEventCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    session: Optional[UserSession] = Depends(get_user_session)
):
    """Track a conversion event."""
    
    conversion = ConversionEvent(
        user_id=current_user.id if current_user else None,
        session_id=session.id if session else None,
        goal_name=conversion_data.goal_name,
        goal_category=conversion_data.goal_category,
        value=conversion_data.value,
        first_touch_source=conversion_data.first_touch_source,
        last_touch_source=conversion_data.last_touch_source,
        conversion_path=conversion_data.conversion_path,
        time_to_conversion=conversion_data.time_to_conversion,
        properties=conversion_data.properties
    )
    
    db.add(conversion)
    
    # Mark session as converted
    if session:
        session.converted = True
    
    db.commit()
    db.refresh(conversion)
    
    return conversion


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    days: int = Query(7, ge=1, le=365),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics data."""
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # User engagement metrics
    total_sessions = db.query(UserSession).filter(
        UserSession.started_at >= start_date
    ).count()
    
    total_page_views = db.query(PageView).filter(
        PageView.viewed_at >= start_date
    ).count()
    
    avg_session_duration = db.query(func.avg(UserSession.duration_seconds)).filter(
        UserSession.started_at >= start_date,
        UserSession.duration_seconds.isnot(None)
    ).scalar() or 0.0
    
    bounce_rate = db.query(func.avg(UserSession.bounce.cast(db.Float))).filter(
        UserSession.started_at >= start_date
    ).scalar() or 0.0
    
    pages_per_session = total_page_views / total_sessions if total_sessions > 0 else 0.0
    
    return_visitors = db.query(UserSession).filter(
        UserSession.started_at >= start_date,
        UserSession.user_id.isnot(None)
    ).distinct(UserSession.user_id).count()
    
    total_visitors = db.query(UserSession).filter(
        UserSession.started_at >= start_date
    ).distinct(UserSession.user_id).count()
    
    return_visitor_rate = return_visitors / total_visitors if total_visitors > 0 else 0.0
    
    engagement_rate = db.query(func.avg(UserSession.engaged.cast(db.Float))).filter(
        UserSession.started_at >= start_date
    ).scalar() or 0.0
    
    conversion_rate = db.query(func.avg(UserSession.converted.cast(db.Float))).filter(
        UserSession.started_at >= start_date
    ).scalar() or 0.0
    
    engagement_metrics = UserEngagementMetrics(
        total_sessions=total_sessions,
        total_page_views=total_page_views,
        avg_session_duration=round(avg_session_duration, 2),
        bounce_rate=round(bounce_rate * 100, 2),
        pages_per_session=round(pages_per_session, 2),
        return_visitor_rate=round(return_visitor_rate * 100, 2),
        engagement_rate=round(engagement_rate * 100, 2),
        conversion_rate=round(conversion_rate * 100, 2)
    )
    
    # Quote generation metrics
    total_quotes = db.query(Quote).filter(Quote.created_at >= start_date).count()
    quotes_today = db.query(Quote).filter(
        Quote.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    quotes_this_week = db.query(Quote).filter(
        Quote.created_at >= end_date - timedelta(days=7)
    ).count()
    
    quotes_this_month = db.query(Quote).filter(
        Quote.created_at >= end_date - timedelta(days=30)
    ).count()
    
    total_users = db.query(User).filter(User.created_at <= end_date).count()
    avg_quotes_per_user = total_quotes / total_users if total_users > 0 else 0.0
    avg_quotes_per_session = total_quotes / total_sessions if total_sessions > 0 else 0.0
    
    quote_metrics = QuoteGenerationMetrics(
        total_quotes=total_quotes,
        quotes_today=quotes_today,
        quotes_this_week=quotes_this_week,
        quotes_this_month=quotes_this_month,
        avg_quotes_per_user=round(avg_quotes_per_user, 2),
        avg_quotes_per_session=round(avg_quotes_per_session, 2),
        most_popular_categories=[],  # TODO: Implement
        most_used_ai_models=[]  # TODO: Implement
    )
    
    # Voice processing metrics
    total_recordings = db.query(VoiceRecording).filter(
        VoiceRecording.created_at >= start_date
    ).count()
    
    recordings_today = db.query(VoiceRecording).filter(
        VoiceRecording.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    recordings_this_week = db.query(VoiceRecording).filter(
        VoiceRecording.created_at >= end_date - timedelta(days=7)
    ).count()
    
    recordings_this_month = db.query(VoiceRecording).filter(
        VoiceRecording.created_at >= end_date - timedelta(days=30)
    ).count()
    
    total_duration_hours = db.query(func.sum(VoiceRecording.duration_seconds)).filter(
        VoiceRecording.created_at >= start_date
    ).scalar() or 0.0
    total_duration_hours = total_duration_hours / 3600  # Convert to hours
    
    avg_recording_duration = db.query(func.avg(VoiceRecording.duration_seconds)).filter(
        VoiceRecording.created_at >= start_date
    ).scalar() or 0.0
    
    voice_metrics = VoiceProcessingMetrics(
        total_recordings=total_recordings,
        recordings_today=recordings_today,
        recordings_this_week=recordings_this_week,
        recordings_this_month=recordings_this_month,
        total_duration_hours=round(total_duration_hours, 2),
        avg_recording_duration=round(avg_recording_duration, 2),
        processing_success_rate=95.0,  # TODO: Calculate actual rate
        avg_processing_time=2.3  # TODO: Calculate actual time
    )
    
    # Real-time metrics
    realtime_metrics = RealtimeMetrics(
        active_users=50,  # TODO: Implement real-time tracking
        active_sessions=75,
        requests_per_minute=120.5,
        quotes_per_minute=2.3,
        voice_uploads_per_minute=0.8,
        avg_response_time=245.0,
        error_rate=0.5,
        timestamp=datetime.utcnow()
    )
    
    return DashboardData(
        overview=engagement_metrics,
        quotes=quote_metrics,
        voice=voice_metrics,
        realtime=realtime_metrics,
        top_pages=[],  # TODO: Implement
        top_referrers=[],  # TODO: Implement
        geographic_data=[],  # TODO: Implement
        device_breakdown=[],  # TODO: Implement
        browser_breakdown=[]  # TODO: Implement
    )


@router.post("/query", response_model=AnalyticsReport)
async def query_analytics(
    query: AnalyticsQuery,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Execute custom analytics query."""
    
    # TODO: Implement comprehensive analytics querying
    # This is a simplified version
    
    metrics = []
    for metric_name in query.metrics:
        value = 0.0
        
        if metric_name == "page_views":
            value = db.query(PageView).filter(
                PageView.viewed_at >= query.start_date,
                PageView.viewed_at <= query.end_date
            ).count()
        elif metric_name == "unique_visitors":
            value = db.query(UserSession).filter(
                UserSession.started_at >= query.start_date,
                UserSession.started_at <= query.end_date
            ).distinct(UserSession.user_id).count()
        elif metric_name == "sessions":
            value = db.query(UserSession).filter(
                UserSession.started_at >= query.start_date,
                UserSession.started_at <= query.end_date
            ).count()
        elif metric_name == "quotes_generated":
            value = db.query(Quote).filter(
                Quote.created_at >= query.start_date,
                Quote.created_at <= query.end_date
            ).count()
        
        metrics.append({
            "name": metric_name,
            "value": value,
            "change": None,
            "change_percentage": None
        })
    
    return AnalyticsReport(
        period=f"{query.start_date.date()} to {query.end_date.date()}",
        start_date=query.start_date,
        end_date=query.end_date,
        metrics=metrics,
        dimensions=None,
        total_records=len(metrics),
        generated_at=datetime.utcnow()
    )


@router.get("/events", response_model=List[AnalyticsEventResponse])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[EventType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List analytics events (admin only)."""
    
    query = db.query(AnalyticsEvent)
    
    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)
    
    if start_date:
        query = query.filter(AnalyticsEvent.timestamp >= start_date)
    
    if end_date:
        query = query.filter(AnalyticsEvent.timestamp <= end_date)
    
    events = query.order_by(AnalyticsEvent.timestamp.desc()).offset(skip).limit(limit).all()
    
    return events


@router.get("/sessions", response_model=List[UserSessionResponse])
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List user sessions (admin only)."""
    
    query = db.query(UserSession)
    
    if user_id:
        query = query.filter(UserSession.user_id == user_id)
    
    if start_date:
        query = query.filter(UserSession.started_at >= start_date)
    
    if end_date:
        query = query.filter(UserSession.started_at <= end_date)
    
    sessions = query.order_by(UserSession.started_at.desc()).offset(skip).limit(limit).all()
    
    return sessions


@router.get("/funnel/{funnel_name}", response_model=FunnelAnalysis)
async def analyze_funnel(
    funnel_name: str,
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Analyze conversion funnel."""
    
    # TODO: Implement funnel analysis
    # This is a placeholder implementation
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    steps = [
        FunnelStep(
            step_name="Landing",
            step_order=1,
            users=1000,
            conversion_rate=100.0,
            drop_off_rate=0.0
        ),
        FunnelStep(
            step_name="Sign Up",
            step_order=2,
            users=250,
            conversion_rate=25.0,
            drop_off_rate=75.0
        ),
        FunnelStep(
            step_name="First Quote",
            step_order=3,
            users=200,
            conversion_rate=20.0,
            drop_off_rate=5.0
        ),
        FunnelStep(
            step_name="Premium Upgrade",
            step_order=4,
            users=50,
            conversion_rate=5.0,
            drop_off_rate=15.0
        )
    ]
    
    return FunnelAnalysis(
        funnel_name=funnel_name,
        total_users=1000,
        completion_rate=5.0,
        steps=steps,
        analysis_period=f"{days} days",
        start_date=start_date,
        end_date=end_date
    )


@router.get("/experiments/{experiment_id}", response_model=List[ABTestResult])
async def get_experiment_results(
    experiment_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get A/B test experiment results."""
    
    # TODO: Implement A/B test analysis
    # This is a placeholder implementation
    
    results = [
        ABTestResult(
            experiment_id=experiment_id,
            variant="control",
            users=500,
            conversion_rate=12.5,
            confidence_level=95.0,
            statistical_significance=True,
            lift=0.0
        ),
        ABTestResult(
            experiment_id=experiment_id,
            variant="variant_a",
            users=485,
            conversion_rate=15.2,
            confidence_level=95.0,
            statistical_significance=True,
            lift=21.6
        )
    ]
    
    return results


@router.get("/me/events", response_model=List[AnalyticsEventResponse])
async def get_my_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    event_type: Optional[EventType] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's analytics events."""
    
    query = db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == current_user.id)
    
    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)
    
    events = query.order_by(AnalyticsEvent.timestamp.desc()).offset(skip).limit(limit).all()
    
    return events