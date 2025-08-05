"""Analytics reporting service for Quote Master Pro."""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc

from src.core.database import get_db_session
from src.core.config import get_settings
from src.api.models.analytics import (
    AnalyticsEvent, 
    UserSession, 
    PageView, 
    ConversionEvent,
    EventType
)
from src.api.models.user import User
from src.api.models.quote import Quote
from src.api.models.voice import VoiceRecording

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalyticsReporter:
    """Generate comprehensive analytics reports."""
    
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache
        self._report_cache = {}
    
    async def generate_dashboard_report(
        self,
        days: int = 7,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive dashboard report."""
        
        try:
            cache_key = f"dashboard_{days}_{user_id or 'all'}"
            
            # Check cache
            if self._is_cached(cache_key):
                return self._get_from_cache(cache_key)
            
            db = get_db_session()
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Build base query filters
            base_filters = [AnalyticsEvent.timestamp >= start_date]
            if user_id:
                base_filters.append(AnalyticsEvent.user_id == user_id)
            
            # Generate all report sections
            overview = await self._generate_overview_metrics(db, base_filters, start_date, end_date)
            user_metrics = await self._generate_user_metrics(db, base_filters, start_date, end_date)
            quote_metrics = await self._generate_quote_metrics(db, base_filters, start_date, end_date)
            voice_metrics = await self._generate_voice_metrics(db, base_filters, start_date, end_date)
            page_analytics = await self._generate_page_analytics(db, base_filters, start_date, end_date)
            conversion_data = await self._generate_conversion_data(db, base_filters, start_date, end_date)
            trend_analysis = await self._generate_trend_analysis(db, base_filters, start_date, end_date)
            
            db.close()
            
            report = {
                "period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "user_filter": user_id
                },
                "overview": overview,
                "users": user_metrics,
                "quotes": quote_metrics,
                "voice": voice_metrics,
                "pages": page_analytics,
                "conversions": conversion_data,
                "trends": trend_analysis,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Cache the report
            self._cache_report(cache_key, report)
            
            return report
            
        except Exception as e:
            logger.error(f"Dashboard report generation failed: {str(e)}")
            return self._generate_fallback_report(days, user_id)
    
    async def _generate_overview_metrics(
        self,
        db: Session,
        base_filters: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate overview metrics."""
        
        # Total events
        total_events = db.query(AnalyticsEvent).filter(*base_filters).count()
        
        # Unique users
        unique_users = db.query(AnalyticsEvent.user_id).filter(
            *base_filters,
            AnalyticsEvent.user_id.isnot(None)
        ).distinct().count()
        
        # Sessions
        session_filters = [UserSession.started_at >= start_date]
        if len(base_filters) > 1:  # Has user filter
            session_filters.append(UserSession.user_id == base_filters[1].right)
        
        total_sessions = db.query(UserSession).filter(*session_filters).count()
        
        # Page views
        page_view_filters = [PageView.viewed_at >= start_date]
        if len(base_filters) > 1:
            page_view_filters.append(PageView.user_id == base_filters[1].right)
        
        total_page_views = db.query(PageView).filter(*page_view_filters).count()
        
        # Average session duration
        avg_session_duration = db.query(func.avg(UserSession.duration_seconds)).filter(
            *session_filters,
            UserSession.duration_seconds.isnot(None)
        ).scalar() or 0.0
        
        # Bounce rate
        bounce_rate = db.query(func.avg(UserSession.bounce.cast(db.Float))).filter(
            *session_filters
        ).scalar() or 0.0
        
        # Engagement rate
        engagement_rate = db.query(func.avg(UserSession.engaged.cast(db.Float))).filter(
            *session_filters
        ).scalar() or 0.0
        
        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "total_sessions": total_sessions,
            "total_page_views": total_page_views,
            "avg_session_duration": round(avg_session_duration, 2),
            "bounce_rate": round(bounce_rate * 100, 2),
            "engagement_rate": round(engagement_rate * 100, 2),
            "pages_per_session": round(total_page_views / max(total_sessions, 1), 2)
        }
    
    async def _generate_user_metrics(
        self,
        db: Session,
        base_filters: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate user-related metrics."""
        
        # New user registrations
        new_users = db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).count()
        
        # Active users (users with events in period)
        active_users = db.query(AnalyticsEvent.user_id).filter(
            *base_filters,
            AnalyticsEvent.user_id.isnot(None)
        ).distinct().count()
        
        # User retention (users who returned)
        # Simplified: users with sessions on multiple days
        returning_users = db.query(UserSession.user_id).filter(
            UserSession.started_at >= start_date,
            UserSession.user_id.isnot(None)
        ).group_by(UserSession.user_id).having(
            func.count(func.distinct(func.date(UserSession.started_at))) > 1
        ).count()
        
        # Top user countries (from session data)
        top_countries = db.query(
            UserSession.country,
            func.count(UserSession.id).label('count')
        ).filter(
            UserSession.started_at >= start_date,
            UserSession.country.isnot(None)
        ).group_by(UserSession.country).order_by(desc('count')).limit(10).all()
        
        # User device types
        device_breakdown = db.query(
            UserSession.device_type,
            func.count(UserSession.id).label('count')
        ).filter(
            UserSession.started_at >= start_date,
            UserSession.device_type.isnot(None)
        ).group_by(UserSession.device_type).all()
        
        return {
            "new_users": new_users,
            "active_users": active_users,
            "returning_users": returning_users,
            "retention_rate": round((returning_users / max(active_users, 1)) * 100, 2),
            "top_countries": [
                {"country": country, "users": count}
                for country, count in top_countries
            ],
            "device_breakdown": [
                {"device": device or "unknown", "count": count}
                for device, count in device_breakdown
            ]
        }
    
    async def _generate_quote_metrics(
        self,
        db: Session,
        base_filters: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate quote-related metrics."""
        
        # Total quotes generated
        quote_events = db.query(AnalyticsEvent).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.QUOTE_GENERATED
        ).count()
        
        # Quote generation success rate
        successful_quotes = db.query(AnalyticsEvent).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.QUOTE_GENERATED,
            AnalyticsEvent.properties['success'].astext == 'true'
        ).count()
        
        success_rate = (successful_quotes / max(quote_events, 1)) * 100
        
        # Average generation time
        avg_generation_time = db.query(
            func.avg(AnalyticsEvent.properties['generation_time'].astext.cast(db.Float))
        ).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.QUOTE_GENERATED,
            AnalyticsEvent.properties['generation_time'].isnot(None)
        ).scalar() or 0.0
        
        # Most used AI models
        ai_model_usage = db.query(
            AnalyticsEvent.properties['ai_model'].astext.label('model'),
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.QUOTE_GENERATED,
            AnalyticsEvent.properties['ai_model'].isnot(None)
        ).group_by('model').order_by(desc('count')).limit(5).all()
        
        # Quote quality distribution
        quality_distribution = db.query(
            func.floor(AnalyticsEvent.value * 10).label('quality_range'),
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.QUOTE_GENERATED,
            AnalyticsEvent.value.isnot(None)
        ).group_by('quality_range').all()
        
        # Daily quote generation trend
        daily_quotes = db.query(
            func.date(AnalyticsEvent.timestamp).label('date'),
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.QUOTE_GENERATED
        ).group_by('date').order_by('date').all()
        
        return {
            "total_quotes": quote_events,
            "success_rate": round(success_rate, 2),
            "avg_generation_time": round(avg_generation_time, 3),
            "ai_model_usage": [
                {"model": model, "count": count}
                for model, count in ai_model_usage
            ],
            "quality_distribution": [
                {"range": f"{int(range_val)}/10", "count": count}
                for range_val, count in quality_distribution
            ],
            "daily_trend": [
                {"date": date.isoformat(), "quotes": count}
                for date, count in daily_quotes
            ]
        }
    
    async def _generate_voice_metrics(
        self,
        db: Session,
        base_filters: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate voice processing metrics."""
        
        # Voice recordings
        voice_recordings = db.query(VoiceRecording).filter(
            VoiceRecording.created_at >= start_date
        ).count()
        
        # Processing events
        voice_events = db.query(AnalyticsEvent).filter(
            *base_filters,
            AnalyticsEvent.event_type.in_([
                EventType.VOICE_RECORDING_COMPLETED,
                EventType.VOICE_PROCESSING_COMPLETED
            ])
        ).count()
        
        # Success rate
        successful_processing = db.query(AnalyticsEvent).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.VOICE_PROCESSING_COMPLETED,
            AnalyticsEvent.properties['success'].astext == 'true'
        ).count()
        
        total_processing = db.query(AnalyticsEvent).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.VOICE_PROCESSING_COMPLETED
        ).count()
        
        processing_success_rate = (successful_processing / max(total_processing, 1)) * 100
        
        # Average processing time
        avg_processing_time = db.query(
            func.avg(AnalyticsEvent.value)
        ).filter(
            *base_filters,
            AnalyticsEvent.event_type == EventType.VOICE_PROCESSING_COMPLETED,
            AnalyticsEvent.value.isnot(None)
        ).scalar() or 0.0
        
        # Total audio duration processed (from voice recordings)
        total_duration = db.query(
            func.sum(VoiceRecording.duration_seconds)
        ).filter(
            VoiceRecording.created_at >= start_date
        ).scalar() or 0.0
        
        return {
            "total_recordings": voice_recordings,
            "total_processing_events": voice_events,
            "processing_success_rate": round(processing_success_rate, 2),
            "avg_processing_time": round(avg_processing_time, 2),
            "total_audio_duration": round(total_duration, 2),
            "avg_recording_duration": round(total_duration / max(voice_recordings, 1), 2)
        }
    
    async def _generate_page_analytics(
        self,
        db: Session,
        base_filters: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate page analytics."""
        
        # Top pages by views
        top_pages = db.query(
            PageView.path,
            func.count(PageView.id).label('views'),
            func.count(func.distinct(PageView.user_id)).label('unique_users')
        ).filter(
            PageView.viewed_at >= start_date
        ).group_by(PageView.path).order_by(desc('views')).limit(10).all()
        
        # Entry pages (landing pages)
        entry_pages = db.query(
            UserSession.landing_page,
            func.count(UserSession.id).label('sessions')
        ).filter(
            UserSession.started_at >= start_date,
            UserSession.landing_page.isnot(None)
        ).group_by(UserSession.landing_page).order_by(desc('sessions')).limit(10).all()
        
        # Exit pages
        exit_pages = db.query(
            UserSession.exit_page,
            func.count(UserSession.id).label('sessions')
        ).filter(
            UserSession.started_at >= start_date,
            UserSession.exit_page.isnot(None)
        ).group_by(UserSession.exit_page).order_by(desc('sessions')).limit(10).all()
        
        # Average page load times
        avg_load_times = db.query(
            PageView.path,
            func.avg(PageView.load_time).label('avg_load_time')
        ).filter(
            PageView.viewed_at >= start_date,
            PageView.load_time.isnot(None)
        ).group_by(PageView.path).order_by(desc('avg_load_time')).limit(10).all()
        
        return {
            "top_pages": [
                {"path": path, "views": views, "unique_users": unique_users}
                for path, views, unique_users in top_pages
            ],
            "entry_pages": [
                {"page": page, "sessions": sessions}
                for page, sessions in entry_pages
            ],
            "exit_pages": [
                {"page": page, "sessions": sessions}
                for page, sessions in exit_pages
            ],
            "page_performance": [
                {"path": path, "avg_load_time": round(float(avg_time), 3)}
                for path, avg_time in avg_load_times if avg_time
            ]
        }
    
    async def _generate_conversion_data(
        self,
        db: Session,
        base_filters: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate conversion analytics."""
        
        # Total conversions
        total_conversions = db.query(ConversionEvent).filter(
            ConversionEvent.converted_at >= start_date
        ).count()
        
        # Conversion by goal
        conversions_by_goal = db.query(
            ConversionEvent.goal_name,
            func.count(ConversionEvent.id).label('count'),
            func.avg(ConversionEvent.value).label('avg_value')
        ).filter(
            ConversionEvent.converted_at >= start_date
        ).group_by(ConversionEvent.goal_name).order_by(desc('count')).all()
        
        # Conversion rate (simplified)
        total_users = db.query(UserSession.user_id).filter(
            UserSession.started_at >= start_date,
            UserSession.user_id.isnot(None)
        ).distinct().count()
        
        conversion_rate = (total_conversions / max(total_users, 1)) * 100
        
        # Daily conversion trend
        daily_conversions = db.query(
            func.date(ConversionEvent.converted_at).label('date'),
            func.count(ConversionEvent.id).label('count')
        ).filter(
            ConversionEvent.converted_at >= start_date
        ).group_by('date').order_by('date').all()
        
        return {
            "total_conversions": total_conversions,
            "conversion_rate": round(conversion_rate, 2),
            "conversions_by_goal": [
                {
                    "goal": goal,
                    "conversions": count,
                    "avg_value": round(float(avg_value), 2) if avg_value else 0.0
                }
                for goal, count, avg_value in conversions_by_goal
            ],
            "daily_trend": [
                {"date": date.isoformat(), "conversions": count}
                for date, count in daily_conversions
            ]
        }
    
    async def _generate_trend_analysis(
        self,
        db: Session,
        base_filters: List[Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate trend analysis."""
        
        # Daily active users
        daily_active_users = db.query(
            func.date(AnalyticsEvent.timestamp).label('date'),
            func.count(func.distinct(AnalyticsEvent.user_id)).label('users')
        ).filter(
            *base_filters,
            AnalyticsEvent.user_id.isnot(None)
        ).group_by('date').order_by('date').all()
        
        # Hourly activity pattern
        hourly_activity = db.query(
            func.extract('hour', AnalyticsEvent.timestamp).label('hour'),
            func.count(AnalyticsEvent.id).label('events')
        ).filter(*base_filters).group_by('hour').order_by('hour').all()
        
        # Weekly pattern
        weekly_pattern = db.query(
            func.extract('dow', AnalyticsEvent.timestamp).label('day_of_week'),
            func.count(AnalyticsEvent.id).label('events')
        ).filter(*base_filters).group_by('day_of_week').order_by('day_of_week').all()
        
        return {
            "daily_active_users": [
                {"date": date.isoformat(), "users": users}
                for date, users in daily_active_users
            ],
            "hourly_activity": [
                {"hour": int(hour), "events": events}
                for hour, events in hourly_activity
            ],
            "weekly_pattern": [
                {"day": int(day), "events": events}
                for day, events in weekly_pattern
            ]
        }
    
    async def generate_user_report(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Generate detailed report for a specific user."""
        
        try:
            db = get_db_session()
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # User basic info
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            # User activity summary
            total_events = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.timestamp >= start_date
            ).count()
            
            # Sessions
            sessions = db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.started_at >= start_date
            ).order_by(desc(UserSession.started_at)).all()
            
            # Quotes generated
            quotes_generated = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_type == EventType.QUOTE_GENERATED,
                AnalyticsEvent.timestamp >= start_date
            ).count()
            
            # Voice recordings
            voice_recordings = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_type == EventType.VOICE_RECORDING_COMPLETED,
                AnalyticsEvent.timestamp >= start_date
            ).count()
            
            # Most active days
            daily_activity = db.query(
                func.date(AnalyticsEvent.timestamp).label('date'),
                func.count(AnalyticsEvent.id).label('events')
            ).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.timestamp >= start_date
            ).group_by('date').order_by(desc('events')).limit(10).all()
            
            db.close()
            
            return {
                "user_id": user_id,
                "user_info": {
                    "email": user.email,
                    "full_name": user.full_name,
                    "created_at": user.created_at.isoformat(),
                    "role": user.role,
                    "subscription_tier": user.subscription_tier
                },
                "period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "activity_summary": {
                    "total_events": total_events,
                    "total_sessions": len(sessions),
                    "quotes_generated": quotes_generated,
                    "voice_recordings": voice_recordings,
                    "avg_session_duration": sum(
                        s.duration_seconds or 0 for s in sessions
                    ) / max(len(sessions), 1)
                },
                "sessions": [
                    {
                        "id": str(session.id),
                        "started_at": session.started_at.isoformat(),
                        "duration_seconds": session.duration_seconds,
                        "page_views": session.page_views,
                        "quotes_generated": session.quotes_generated,
                        "device_type": session.device_type,
                        "country": session.country
                    }
                    for session in sessions[:10]  # Last 10 sessions
                ],
                "daily_activity": [
                    {"date": date.isoformat(), "events": events}
                    for date, events in daily_activity
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"User report generation failed: {str(e)}")
            return {"error": str(e)}
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if report is cached and still valid."""
        
        if cache_key not in self._report_cache:
            return False
        
        cached_data = self._report_cache[cache_key]
        cached_time = datetime.fromisoformat(cached_data["cached_at"])
        
        return datetime.utcnow() - cached_time < timedelta(seconds=self.cache_duration)
    
    def _get_from_cache(self, cache_key: str) -> Dict[str, Any]:
        """Get report from cache."""
        
        cached_data = self._report_cache[cache_key]
        cached_data["from_cache"] = True
        return cached_data["data"]
    
    def _cache_report(self, cache_key: str, report: Dict[str, Any]) -> None:
        """Cache a report."""
        
        self._report_cache[cache_key] = {
            "data": report,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        # Clean old cache entries
        self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Clean up old cache entries."""
        
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, data in self._report_cache.items():
            cached_time = datetime.fromisoformat(data["cached_at"])
            if current_time - cached_time > timedelta(seconds=self.cache_duration * 2):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._report_cache[key]
    
    def _generate_fallback_report(self, days: int, user_id: Optional[str]) -> Dict[str, Any]:
        """Generate a fallback report when main generation fails."""
        
        return {
            "period": {
                "days": days,
                "user_filter": user_id
            },
            "overview": {
                "total_events": 0,
                "unique_users": 0,
                "total_sessions": 0,
                "total_page_views": 0
            },
            "error": "Report generation failed, showing empty report",
            "generated_at": datetime.utcnow().isoformat()
        }


# Global reporter instance
_reporter = None


def get_analytics_reporter() -> AnalyticsReporter:
    """Get the global analytics reporter instance."""
    global _reporter
    if _reporter is None:
        _reporter = AnalyticsReporter()
    return _reporter