"""Analytics tracking service for Quote Master Pro."""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

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

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalyticsTracker:
    """Real-time analytics tracking service."""
    
    def __init__(self):
        self.event_queue = asyncio.Queue()
        self.batch_size = 100
        self.flush_interval = 30  # seconds
        self.is_processing = False
        self._active_sessions = {}
        self._event_buffer = []
        
    async def track_event(
        self,
        event_type: EventType,
        event_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track an analytics event."""
        
        try:
            event_data = {
                "event_type": event_type,
                "event_name": event_name,
                "user_id": user_id,
                "session_id": session_id,
                "properties": properties or {},
                "value": value,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            # Add to queue for processing
            await self.event_queue.put(event_data)
            
            # Log important events immediately
            if event_type in [EventType.USER_REGISTER, EventType.QUOTE_GENERATED, EventType.VOICE_RECORDING_COMPLETED]:
                logger.info(f"Important event tracked: {event_name} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track event {event_name}: {str(e)}")
            return False
    
    async def track_page_view(
        self,
        url: str,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        referrer: Optional[str] = None,
        load_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track a page view."""
        
        try:
            # Extract path from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            path = parsed_url.path
            
            page_view_data = {
                "type": "page_view",
                "url": url,
                "path": path,
                "title": title,
                "user_id": user_id,
                "session_id": session_id,
                "referrer": referrer,
                "load_time": load_time,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            await self.event_queue.put(page_view_data)
            
            # Update session activity
            if session_id:
                await self._update_session_activity(session_id, user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to track page view for {url}: {str(e)}")
            return False
    
    async def track_user_action(
        self,
        action: str,
        user_id: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """Track a user action."""
        
        return await self.track_event(
            event_type=EventType.FEATURE_USED,
            event_name=f"user_action_{action}",
            user_id=user_id,
            session_id=session_id,
            properties={
                "action": action,
                "target_type": target_type,
                "target_id": target_id,
                **(properties or {})
            }
        )
    
    async def track_quote_generation(
        self,
        user_id: str,
        quote_id: str,
        ai_model: str,
        generation_time: float,
        quality_score: Optional[float] = None,
        session_id: Optional[str] = None,
        prompt_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track quote generation with detailed metrics."""
        
        return await self.track_event(
            event_type=EventType.QUOTE_GENERATED,
            event_name="quote_generated",
            user_id=user_id,
            session_id=session_id,
            value=quality_score,
            properties={
                "quote_id": quote_id,
                "ai_model": ai_model,
                "generation_time": generation_time,
                "quality_score": quality_score,
                "prompt_data": prompt_data or {}
            }
        )
    
    async def track_voice_processing(
        self,
        user_id: str,
        recording_id: str,
        processing_type: str,
        processing_time: float,
        success: bool,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track voice processing events."""
        
        event_type = EventType.VOICE_PROCESSING_COMPLETED if success else EventType.AI_ERROR_OCCURRED
        
        return await self.track_event(
            event_type=event_type,
            event_name=f"voice_{processing_type}_{'completed' if success else 'failed'}",
            user_id=user_id,
            session_id=session_id,
            value=processing_time,
            properties={
                "recording_id": recording_id,
                "processing_type": processing_type,
                "processing_time": processing_time,
                "success": success,
                **(metadata or {})
            }
        )
    
    async def track_conversion(
        self,
        user_id: str,
        goal_name: str,
        goal_category: Optional[str] = None,
        value: Optional[float] = None,
        session_id: Optional[str] = None,
        conversion_path: Optional[List[str]] = None
    ) -> bool:
        """Track conversion events."""
        
        conversion_data = {
            "type": "conversion",
            "user_id": user_id,
            "session_id": session_id,
            "goal_name": goal_name,
            "goal_category": goal_category,
            "value": value,
            "conversion_path": conversion_path or [],
            "timestamp": datetime.utcnow()
        }
        
        await self.event_queue.put(conversion_data)
        
        return True
    
    async def start_session(
        self,
        user_id: Optional[str] = None,
        session_token: Optional[str] = None,
        anonymous_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new user session."""
        
        try:
            session_id = session_token or str(uuid.uuid4())
            
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "anonymous_id": anonymous_id or str(uuid.uuid4()),
                "started_at": datetime.utcnow(),
                "metadata": metadata or {},
                "page_views": 0,
                "quotes_generated": 0,
                "voice_recordings": 0,
                "interactions": 0
            }
            
            # Store in active sessions cache
            self._active_sessions[session_id] = session_data
            
            # Track session start event
            await self.track_event(
                event_type=EventType.SESSION_STARTED,
                event_name="session_started",
                user_id=user_id,
                session_id=session_id,
                properties={"anonymous_id": anonymous_id}
            )
            
            # Queue session creation for database
            db_session_data = {
                "type": "session_start",
                "session_data": session_data
            }
            await self.event_queue.put(db_session_data)
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start session: {str(e)}")
            return str(uuid.uuid4())  # Return a basic session ID
    
    async def end_session(self, session_id: str) -> bool:
        """End a user session."""
        
        try:
            if session_id not in self._active_sessions:
                logger.warning(f"Attempting to end unknown session: {session_id}")
                return False
            
            session_data = self._active_sessions[session_id]
            session_data["ended_at"] = datetime.utcnow()
            
            # Calculate session duration
            duration = session_data["ended_at"] - session_data["started_at"]
            session_data["duration_seconds"] = int(duration.total_seconds())
            
            # Determine session quality
            session_data["bounce"] = session_data["page_views"] <= 1 and session_data["duration_seconds"] < 30
            session_data["engaged"] = (
                session_data["page_views"] > 2 or 
                session_data["duration_seconds"] > 120 or
                session_data["quotes_generated"] > 0 or
                session_data["voice_recordings"] > 0
            )
            
            # Track session end event
            await self.track_event(
                event_type=EventType.SESSION_ENDED,
                event_name="session_ended",
                user_id=session_data["user_id"],
                session_id=session_id,
                value=session_data["duration_seconds"],
                properties={
                    "duration_seconds": session_data["duration_seconds"],
                    "page_views": session_data["page_views"],
                    "quotes_generated": session_data["quotes_generated"],
                    "voice_recordings": session_data["voice_recordings"],
                    "bounce": session_data["bounce"],
                    "engaged": session_data["engaged"]
                }
            )
            
            # Queue session end for database
            db_session_data = {
                "type": "session_end",
                "session_data": session_data
            }
            await self.event_queue.put(db_session_data)
            
            # Remove from active sessions
            del self._active_sessions[session_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {str(e)}")
            return False
    
    async def _update_session_activity(self, session_id: str, user_id: Optional[str] = None) -> None:
        """Update session activity."""
        
        if session_id in self._active_sessions:
            session_data = self._active_sessions[session_id]
            session_data["last_activity"] = datetime.utcnow()
            session_data["page_views"] += 1
            
            # Update user_id if provided and not set
            if user_id and not session_data.get("user_id"):
                session_data["user_id"] = user_id
    
    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session metrics."""
        
        return self._active_sessions.get(session_id)
    
    async def start_processing(self) -> None:
        """Start the background event processing."""
        
        if self.is_processing:
            logger.warning("Analytics processing already started")
            return
        
        self.is_processing = True
        
        # Start background tasks
        asyncio.create_task(self._process_event_queue())
        asyncio.create_task(self._periodic_flush())
        asyncio.create_task(self._cleanup_old_sessions())
        
        logger.info("Analytics processing started")
    
    async def stop_processing(self) -> None:
        """Stop the background event processing."""
        
        self.is_processing = False
        
        # Flush remaining events
        await self._flush_events()
        
        logger.info("Analytics processing stopped")
    
    async def _process_event_queue(self) -> None:
        """Process events from the queue."""
        
        while self.is_processing:
            try:
                # Get events with timeout
                events_batch = []
                
                for _ in range(self.batch_size):
                    try:
                        event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                        events_batch.append(event)
                    except asyncio.TimeoutError:
                        break
                
                if events_batch:
                    await self._process_events_batch(events_batch)
                
            except Exception as e:
                logger.error(f"Event processing error: {str(e)}")
                await asyncio.sleep(1.0)
    
    async def _process_events_batch(self, events: List[Dict[str, Any]]) -> None:
        """Process a batch of events."""
        
        try:
            db = get_db_session()
            
            for event_data in events:
                await self._process_single_event(event_data, db)
            
            # Commit all events in batch
            db.commit()
            db.close()
            
            logger.debug(f"Processed batch of {len(events)} events")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            if db:
                db.rollback()
                db.close()
    
    async def _process_single_event(self, event_data: Dict[str, Any], db: Session) -> None:
        """Process a single event."""
        
        event_type = event_data.get("type", "analytics_event")
        
        if event_type == "analytics_event":
            await self._create_analytics_event(event_data, db)
        elif event_type == "page_view":
            await self._create_page_view(event_data, db)
        elif event_type == "conversion":
            await self._create_conversion_event(event_data, db)
        elif event_type == "session_start":
            await self._create_user_session(event_data["session_data"], db)
        elif event_type == "session_end":
            await self._update_user_session(event_data["session_data"], db)
    
    async def _create_analytics_event(self, event_data: Dict[str, Any], db: Session) -> None:
        """Create analytics event in database."""
        
        event = AnalyticsEvent(
            user_id=event_data.get("user_id"),
            session_id=event_data.get("session_id"),
            event_type=event_data["event_type"],
            event_name=event_data["event_name"],
            properties=event_data.get("properties"),
            value=event_data.get("value"),
            timestamp=event_data["timestamp"]
        )
        
        # Add metadata if available
        metadata = event_data.get("metadata", {})
        if "user_agent" in metadata:
            event.user_agent = metadata["user_agent"]
        if "ip_address" in metadata:
            event.ip_address = metadata["ip_address"]
        if "page_url" in metadata:
            event.page_url = metadata["page_url"]
        
        db.add(event)
    
    async def _create_page_view(self, event_data: Dict[str, Any], db: Session) -> None:
        """Create page view in database."""
        
        page_view = PageView(
            user_id=event_data.get("user_id"),
            session_id=event_data.get("session_id"),
            url=event_data["url"],
            title=event_data.get("title"),
            path=event_data["path"],
            referrer=event_data.get("referrer"),
            load_time=event_data.get("load_time"),
            viewed_at=event_data["timestamp"]
        )
        
        db.add(page_view)
    
    async def _create_conversion_event(self, event_data: Dict[str, Any], db: Session) -> None:
        """Create conversion event in database."""
        
        conversion = ConversionEvent(
            user_id=event_data.get("user_id"),
            session_id=event_data.get("session_id"),
            goal_name=event_data["goal_name"],
            goal_category=event_data.get("goal_category"),
            value=event_data.get("value"),
            conversion_path=event_data.get("conversion_path"),
            converted_at=event_data["timestamp"]
        )
        
        db.add(conversion)
    
    async def _create_user_session(self, session_data: Dict[str, Any], db: Session) -> None:
        """Create user session in database."""
        
        session = UserSession(
            id=session_data["session_id"],
            user_id=session_data.get("user_id"),
            session_token=session_data["session_id"],
            anonymous_id=session_data.get("anonymous_id"),
            started_at=session_data["started_at"]
        )
        
        # Add metadata
        metadata = session_data.get("metadata", {})
        if "user_agent" in metadata:
            session.user_agent = metadata["user_agent"]
        if "ip_address" in metadata:
            session.ip_address = metadata["ip_address"]
        if "referrer" in metadata:
            session.referrer = metadata["referrer"]
        
        db.add(session)
    
    async def _update_user_session(self, session_data: Dict[str, Any], db: Session) -> None:
        """Update user session in database."""
        
        session = db.query(UserSession).filter(
            UserSession.id == session_data["session_id"]
        ).first()
        
        if session:
            session.ended_at = session_data["ended_at"]
            session.duration_seconds = session_data["duration_seconds"]
            session.page_views = session_data["page_views"]
            session.quotes_generated = session_data["quotes_generated"]
            session.voice_recordings = session_data["voice_recordings"]
            session.interactions = session_data["interactions"]
            session.bounce = session_data["bounce"]
            session.engaged = session_data["engaged"]
            session.is_active = False
    
    async def _periodic_flush(self) -> None:
        """Periodically flush events."""
        
        while self.is_processing:
            await asyncio.sleep(self.flush_interval)
            await self._flush_events()
    
    async def _flush_events(self) -> None:
        """Flush buffered events."""
        
        if self._event_buffer:
            try:
                await self._process_events_batch(self._event_buffer)
                self._event_buffer.clear()
                logger.debug("Event buffer flushed")
            except Exception as e:
                logger.error(f"Event flush failed: {str(e)}")
    
    async def _cleanup_old_sessions(self) -> None:
        """Clean up old inactive sessions."""
        
        while self.is_processing:
            try:
                current_time = datetime.utcnow()
                expired_sessions = []
                
                # Find sessions inactive for more than 30 minutes
                for session_id, session_data in self._active_sessions.items():
                    last_activity = session_data.get("last_activity", session_data["started_at"])
                    if current_time - last_activity > timedelta(minutes=30):
                        expired_sessions.append(session_id)
                
                # End expired sessions
                for session_id in expired_sessions:
                    await self.end_session(session_id)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
            except Exception as e:
                logger.error(f"Session cleanup error: {str(e)}")
            
            # Run cleanup every 10 minutes
            await asyncio.sleep(600)
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get current analytics summary."""
        
        return {
            "active_sessions": len(self._active_sessions),
            "queue_size": self.event_queue.qsize(),
            "buffer_size": len(self._event_buffer),
            "is_processing": self.is_processing,
            "recent_sessions": [
                {
                    "session_id": sid,
                    "user_id": data.get("user_id"),
                    "started_at": data["started_at"].isoformat(),
                    "page_views": data["page_views"],
                    "quotes_generated": data["quotes_generated"]
                }
                for sid, data in list(self._active_sessions.items())[-5:]
            ]
        }


# Global tracker instance
_tracker = None


def get_analytics_tracker() -> AnalyticsTracker:
    """Get the global analytics tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = AnalyticsTracker()
    return _tracker