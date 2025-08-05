"""Analytics Pydantic schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator
from uuid import UUID

from src.api.models.analytics import EventType


class AnalyticsEventBase(BaseModel):
    """Base analytics event schema."""
    event_type: EventType
    event_name: str
    event_category: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    value: Optional[float] = None


class AnalyticsEventCreate(AnalyticsEventBase):
    """Analytics event creation schema."""
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    screen_resolution: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    page_load_time: Optional[float] = None
    api_response_time: Optional[float] = None
    experiment_id: Optional[str] = None
    variant: Optional[str] = None


class AnalyticsEventResponse(AnalyticsEventBase):
    """Analytics event response schema."""
    id: UUID
    user_id: Optional[UUID]
    session_id: Optional[UUID]
    page_url: Optional[str]
    page_title: Optional[str]
    referrer: Optional[str]
    user_agent: Optional[str]
    ip_address: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    operating_system: Optional[str]
    screen_resolution: Optional[str]
    country: Optional[str]
    region: Optional[str]
    city: Optional[str]
    timezone: Optional[str]
    page_load_time: Optional[float]
    api_response_time: Optional[float]
    experiment_id: Optional[str]
    variant: Optional[str]
    timestamp: datetime
    server_timestamp: datetime
    
    class Config:
        from_attributes = True


class UserSessionBase(BaseModel):
    """Base user session schema."""
    landing_page: Optional[str] = None
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class UserSessionCreate(UserSessionBase):
    """User session creation schema."""
    anonymous_id: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None


class UserSessionUpdate(BaseModel):
    """User session update schema."""
    exit_page: Optional[str] = None
    page_views: Optional[int] = None
    quotes_generated: Optional[int] = None
    voice_recordings: Optional[int] = None
    interactions: Optional[int] = None


class UserSessionResponse(UserSessionBase):
    """User session response schema."""
    id: UUID
    user_id: Optional[UUID]
    session_token: str
    anonymous_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    last_activity_at: datetime
    duration_seconds: Optional[int]
    exit_page: Optional[str]
    user_agent: Optional[str]
    ip_address: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    operating_system: Optional[str]
    country: Optional[str]
    region: Optional[str]
    city: Optional[str]
    timezone: Optional[str]
    page_views: int
    quotes_generated: int
    voice_recordings: int
    interactions: int
    bounce: bool
    engaged: bool
    converted: bool
    is_active: bool
    
    class Config:
        from_attributes = True


class PageViewCreate(BaseModel):
    """Page view creation schema."""
    url: str
    title: Optional[str] = None
    path: str
    query_params: Optional[Dict[str, Any]] = None
    referrer: Optional[str] = None
    previous_page: Optional[str] = None
    time_on_page: Optional[float] = None
    load_time: Optional[float] = None
    scroll_depth: Optional[float] = Field(None, ge=0.0, le=100.0)
    clicks: int = 0
    interactions: int = 0


class PageViewResponse(BaseModel):
    """Page view response schema."""
    id: UUID
    user_id: Optional[UUID]
    session_id: Optional[UUID]
    url: str
    title: Optional[str]
    path: str
    query_params: Optional[Dict[str, Any]]
    referrer: Optional[str]
    previous_page: Optional[str]
    viewed_at: datetime
    time_on_page: Optional[float]
    load_time: Optional[float]
    scroll_depth: Optional[float]
    clicks: int
    interactions: int
    
    class Config:
        from_attributes = True


class ConversionEventCreate(BaseModel):
    """Conversion event creation schema."""
    goal_name: str
    goal_category: Optional[str] = None
    value: Optional[float] = None
    first_touch_source: Optional[str] = None
    last_touch_source: Optional[str] = None
    conversion_path: Optional[List[str]] = None
    time_to_conversion: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None


class ConversionEventResponse(BaseModel):
    """Conversion event response schema."""
    id: UUID
    user_id: Optional[UUID]
    session_id: Optional[UUID]
    goal_name: str
    goal_category: Optional[str]
    value: Optional[float]
    first_touch_source: Optional[str]
    last_touch_source: Optional[str]
    conversion_path: Optional[List[str]]
    converted_at: datetime
    time_to_conversion: Optional[int]
    properties: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class AnalyticsQuery(BaseModel):
    """Analytics query schema."""
    start_date: datetime
    end_date: datetime
    metrics: List[str] = Field(..., min_items=1)
    dimensions: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(None, regex="^(asc|desc)$")
    limit: int = Field(100, ge=1, le=1000)
    
    @validator('metrics')
    def validate_metrics(cls, v):
        valid_metrics = [
            'page_views', 'unique_visitors', 'sessions', 'bounce_rate',
            'avg_session_duration', 'quotes_generated', 'voice_recordings',
            'conversions', 'revenue', 'engagement_rate'
        ]
        for metric in v:
            if metric not in valid_metrics:
                raise ValueError(f'Invalid metric: {metric}')
        return v


class AnalyticsMetric(BaseModel):
    """Analytics metric schema."""
    name: str
    value: float
    change: Optional[float] = None
    change_percentage: Optional[float] = None


class AnalyticsDimension(BaseModel):
    """Analytics dimension schema."""
    name: str
    values: List[Dict[str, Any]]


class AnalyticsReport(BaseModel):
    """Analytics report schema."""
    period: str
    start_date: datetime
    end_date: datetime
    metrics: List[AnalyticsMetric]
    dimensions: Optional[List[AnalyticsDimension]] = None
    total_records: int
    generated_at: datetime


class UserEngagementMetrics(BaseModel):
    """User engagement metrics schema."""
    total_sessions: int
    total_page_views: int
    avg_session_duration: float
    bounce_rate: float
    pages_per_session: float
    return_visitor_rate: float
    engagement_rate: float
    conversion_rate: float


class QuoteGenerationMetrics(BaseModel):
    """Quote generation metrics schema."""
    total_quotes: int
    quotes_today: int
    quotes_this_week: int
    quotes_this_month: int
    avg_quotes_per_user: float
    avg_quotes_per_session: float
    most_popular_categories: List[Dict[str, Any]]
    most_used_ai_models: List[Dict[str, Any]]


class VoiceProcessingMetrics(BaseModel):
    """Voice processing metrics schema."""
    total_recordings: int
    recordings_today: int
    recordings_this_week: int
    recordings_this_month: int
    total_duration_hours: float
    avg_recording_duration: float
    processing_success_rate: float
    avg_processing_time: float


class RealtimeMetrics(BaseModel):
    """Real-time metrics schema."""
    active_users: int
    active_sessions: int
    requests_per_minute: float
    quotes_per_minute: float
    voice_uploads_per_minute: float
    avg_response_time: float
    error_rate: float
    timestamp: datetime


class DashboardData(BaseModel):
    """Dashboard data schema."""
    overview: UserEngagementMetrics
    quotes: QuoteGenerationMetrics
    voice: VoiceProcessingMetrics
    realtime: RealtimeMetrics
    top_pages: List[Dict[str, Any]]
    top_referrers: List[Dict[str, Any]]
    geographic_data: List[Dict[str, Any]]
    device_breakdown: List[Dict[str, Any]]
    browser_breakdown: List[Dict[str, Any]]


class FunnelStep(BaseModel):
    """Funnel step schema."""
    step_name: str
    step_order: int
    users: int
    conversion_rate: float
    drop_off_rate: float


class FunnelAnalysis(BaseModel):
    """Funnel analysis schema."""
    funnel_name: str
    total_users: int
    completion_rate: float
    steps: List[FunnelStep]
    analysis_period: str
    start_date: datetime
    end_date: datetime


class ABTestResult(BaseModel):
    """A/B test result schema."""
    experiment_id: str
    variant: str
    users: int
    conversion_rate: float
    confidence_level: float
    statistical_significance: bool
    lift: float