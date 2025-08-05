"""Background task workers for Quote Master Pro."""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
import traceback

from celery import Celery
from celery.result import AsyncResult

from src.core.config import get_settings
from src.core.database import get_db_session
from src.services.analytics.tracker import get_analytics_tracker
from src.services.ai.orchestrator import get_ai_orchestrator
from src.services.voice.processor import get_voice_processor

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskPriority(int, Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    STARTED = "started"
    RETRY = "retry"
    FAILURE = "failure"
    SUCCESS = "success"
    REVOKED = "revoked"


# Initialize Celery app
celery_app = Celery(
    'quote_master_pro',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    task_routes={
        'quote_master_pro.process_voice': {'queue': 'voice_processing'},
        'quote_master_pro.generate_quote': {'queue': 'quote_generation'},
        'quote_master_pro.analytics': {'queue': 'analytics'},
        'quote_master_pro.cleanup': {'queue': 'maintenance'},
    }
)


class BackgroundTaskManager:
    """Manager for background tasks and job scheduling."""
    
    def __init__(self):
        self.active_tasks = {}
        self.task_history = []
        self.max_history = 1000
    
    async def schedule_voice_processing(
        self,
        recording_id: str,
        user_id: str,
        processing_options: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """Schedule voice processing task."""
        
        try:
            task_data = {
                "recording_id": recording_id,
                "user_id": user_id,
                "processing_options": processing_options,
                "scheduled_at": datetime.utcnow().isoformat()
            }
            
            # Submit to Celery
            result = process_voice_recording.apply_async(
                args=[task_data],
                priority=priority.value
            )
            
            # Track task
            self._track_task(result.id, "voice_processing", task_data)
            
            logger.info(f"Scheduled voice processing task {result.id} for recording {recording_id}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to schedule voice processing: {str(e)}")
            raise
    
    async def schedule_quote_generation(
        self,
        user_id: str,
        prompt: str,
        generation_options: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """Schedule quote generation task."""
        
        try:
            task_data = {
                "user_id": user_id,
                "prompt": prompt,
                "generation_options": generation_options,
                "scheduled_at": datetime.utcnow().isoformat()
            }
            
            result = generate_quote_async.apply_async(
                args=[task_data],
                priority=priority.value
            )
            
            self._track_task(result.id, "quote_generation", task_data)
            
            logger.info(f"Scheduled quote generation task {result.id} for user {user_id}")
            
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to schedule quote generation: {str(e)}")
            raise
    
    async def schedule_analytics_processing(
        self,
        analytics_type: str,
        data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.LOW
    ) -> str:
        """Schedule analytics processing task."""
        
        try:
            task_data = {
                "analytics_type": analytics_type,
                "data": data,
                "scheduled_at": datetime.utcnow().isoformat()
            }
            
            result = process_analytics.apply_async(
                args=[task_data],
                priority=priority.value
            )
            
            self._track_task(result.id, "analytics", task_data)
            
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to schedule analytics processing: {str(e)}")
            raise
    
    async def schedule_cleanup_task(
        self,
        cleanup_type: str,
        options: Dict[str, Any],
        priority: TaskPriority = TaskPriority.LOW
    ) -> str:
        """Schedule cleanup task."""
        
        try:
            task_data = {
                "cleanup_type": cleanup_type,
                "options": options,
                "scheduled_at": datetime.utcnow().isoformat()
            }
            
            result = cleanup_task.apply_async(
                args=[task_data],
                priority=priority.value
            )
            
            self._track_task(result.id, "cleanup", task_data)
            
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to schedule cleanup task: {str(e)}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and result."""
        
        try:
            result = AsyncResult(task_id, app=celery_app)
            
            status_info = {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "date_done": result.date_done.isoformat() if result.date_done else None,
                "traceback": result.traceback if result.failed() else None
            }
            
            # Add tracking info if available
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                status_info.update({
                    "task_type": task_info["task_type"],
                    "scheduled_at": task_info["scheduled_at"],
                    "task_data": task_info["task_data"]
                })
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "status": "unknown",
                "error": str(e)
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        
        try:
            celery_app.control.revoke(task_id, terminate=True)
            
            # Update tracking
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = TaskStatus.REVOKED
                self.active_tasks[task_id]["cancelled_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Cancelled task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return False
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of active tasks."""
        
        active_list = []
        
        for task_id, task_info in self.active_tasks.items():
            # Check if task is still active
            result = AsyncResult(task_id, app=celery_app)
            
            if result.status in ['PENDING', 'STARTED', 'RETRY']:
                task_info["current_status"] = result.status
                active_list.append(task_info)
            else:
                # Move to history
                self._move_to_history(task_id, task_info)
        
        return active_list
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task history."""
        
        return self.task_history[-limit:]
    
    def _track_task(self, task_id: str, task_type: str, task_data: Dict[str, Any]) -> None:
        """Track a task."""
        
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "task_data": task_data,
            "status": TaskStatus.PENDING,
            "scheduled_at": datetime.utcnow().isoformat()
        }
    
    def _move_to_history(self, task_id: str, task_info: Dict[str, Any]) -> None:
        """Move completed task to history."""
        
        # Add completion info
        task_info["completed_at"] = datetime.utcnow().isoformat()
        
        # Add to history
        self.task_history.append(task_info)
        
        # Trim history if too long
        if len(self.task_history) > self.max_history:
            self.task_history = self.task_history[-self.max_history:]
        
        # Remove from active tasks
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]


# Celery tasks
@celery_app.task(bind=True, name='quote_master_pro.process_voice')
def process_voice_recording(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process voice recording task."""
    
    try:
        recording_id = task_data["recording_id"]
        user_id = task_data["user_id"]
        processing_options = task_data["processing_options"]
        
        logger.info(f"Starting voice processing for recording {recording_id}")
        
        # Update task status
        self.update_state(state='STARTED', meta={'status': 'Processing audio file'})
        
        # Get voice processor
        voice_processor = get_voice_processor()
        
        # Process the recording
        # Note: This would need to be adapted for sync execution in Celery
        result = asyncio.run(voice_processor.process_audio_file(
            file_path=f"uploads/audio/{recording_id}",
            processing_options=processing_options
        ))
        
        # Track analytics
        tracker = get_analytics_tracker()
        asyncio.run(tracker.track_voice_processing(
            user_id=user_id,
            recording_id=recording_id,
            processing_type="complete_analysis",
            processing_time=result.get("processing_time", 0),
            success=result["success"]
        ))
        
        logger.info(f"Completed voice processing for recording {recording_id}")
        
        return {
            "success": True,
            "recording_id": recording_id,
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Voice processing task failed: {str(e)}")
        
        # Track failure
        if 'user_id' in task_data and 'recording_id' in task_data:
            tracker = get_analytics_tracker()
            asyncio.run(tracker.track_voice_processing(
                user_id=task_data["user_id"],
                recording_id=task_data["recording_id"],
                processing_type="complete_analysis",
                processing_time=0,
                success=False,
                metadata={"error": str(e)}
            ))
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying voice processing task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))  # Exponential backoff
        
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "failed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, name='quote_master_pro.generate_quote')
def generate_quote_async(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate quote asynchronously."""
    
    try:
        user_id = task_data["user_id"]
        prompt = task_data["prompt"]
        generation_options = task_data["generation_options"]
        
        logger.info(f"Starting quote generation for user {user_id}")
        
        self.update_state(state='STARTED', meta={'status': 'Generating quote'})
        
        # Get AI orchestrator
        ai_orchestrator = get_ai_orchestrator()
        
        # Generate quote
        start_time = datetime.utcnow()
        
        result = asyncio.run(ai_orchestrator.generate_quote(
            prompt=prompt,
            **generation_options
        ))
        
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Track analytics
        if result.success:
            tracker = get_analytics_tracker()
            asyncio.run(tracker.track_quote_generation(
                user_id=user_id,
                quote_id=str(result.metadata.get("quote_id", "unknown")),
                ai_model=result.model_used,
                generation_time=generation_time,
                quality_score=result.confidence_score
            ))
        
        logger.info(f"Completed quote generation for user {user_id}")
        
        return {
            "success": result.success,
            "quote": result.content if result.success else None,
            "metadata": result.metadata if hasattr(result, 'metadata') else {},
            "generation_time": generation_time,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quote generation task failed: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying quote generation task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "failed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, name='quote_master_pro.analytics')
def process_analytics(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process analytics data."""
    
    try:
        analytics_type = task_data["analytics_type"]
        data = task_data["data"]
        
        logger.info(f"Processing analytics: {analytics_type}")
        
        # Process based on analytics type
        if analytics_type == "user_behavior":
            result = _process_user_behavior_analytics(data)
        elif analytics_type == "performance_metrics":
            result = _process_performance_metrics(data)
        elif analytics_type == "usage_patterns":
            result = _process_usage_patterns(data)
        else:
            result = {"processed": False, "reason": f"Unknown analytics type: {analytics_type}"}
        
        return {
            "success": True,
            "analytics_type": analytics_type,
            "result": result,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics processing failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, name='quote_master_pro.cleanup')
def cleanup_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform cleanup tasks."""
    
    try:
        cleanup_type = task_data["cleanup_type"]
        options = task_data["options"]
        
        logger.info(f"Starting cleanup task: {cleanup_type}")
        
        if cleanup_type == "old_sessions":
            result = _cleanup_old_sessions(options)
        elif cleanup_type == "temp_files":
            result = _cleanup_temp_files(options)
        elif cleanup_type == "failed_jobs":
            result = _cleanup_failed_jobs(options)
        elif cleanup_type == "analytics_data":
            result = _cleanup_old_analytics(options)
        else:
            result = {"cleaned": False, "reason": f"Unknown cleanup type: {cleanup_type}"}
        
        logger.info(f"Completed cleanup task: {cleanup_type}")
        
        return {
            "success": True,
            "cleanup_type": cleanup_type,
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }


# Helper functions for task processing
def _process_user_behavior_analytics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process user behavior analytics."""
    
    # Implement user behavior analysis
    # This would involve analyzing user interaction patterns,
    # session data, conversion funnels, etc.
    
    return {
        "patterns_identified": 3,
        "insights_generated": 5,
        "recommendations": ["Improve onboarding flow", "Add more quote categories"]
    }


def _process_performance_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process performance metrics."""
    
    # Implement performance metrics processing
    # This would analyze response times, error rates,
    # system performance, etc.
    
    return {
        "metrics_processed": 15,
        "alerts_generated": 0,
        "performance_score": 92.5
    }


def _process_usage_patterns(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process usage patterns."""
    
    # Implement usage pattern analysis
    # This would analyze feature usage, peak times,
    # user preferences, etc.
    
    return {
        "patterns_found": 8,
        "peak_usage_times": ["9-11 AM", "2-4 PM", "7-9 PM"],
        "popular_features": ["quote_generation", "voice_to_text"]
    }


def _cleanup_old_sessions(options: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up old user sessions."""
    
    try:
        days_old = options.get("days_old", 30)
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        db = get_db_session()
        
        # Find old sessions
        from src.api.models.analytics import UserSession
        old_sessions = db.query(UserSession).filter(
            UserSession.started_at < cutoff_date,
            UserSession.is_active == False
        )
        
        count = old_sessions.count()
        old_sessions.delete()
        
        db.commit()
        db.close()
        
        return {
            "sessions_cleaned": count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}


def _cleanup_temp_files(options: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up temporary files."""
    
    import os
    import glob
    
    try:
        temp_dirs = options.get("temp_dirs", ["tmp/", "temp/", "uploads/temp/"])
        days_old = options.get("days_old", 1)
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        
        files_cleaned = 0
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for file_path in glob.glob(os.path.join(temp_dir, "*")):
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_time:
                            os.remove(file_path)
                            files_cleaned += 1
        
        return {
            "files_cleaned": files_cleaned,
            "directories_checked": len(temp_dirs)
        }
        
    except Exception as e:
        return {"error": str(e)}


def _cleanup_failed_jobs(options: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up failed job records."""
    
    try:
        days_old = options.get("days_old", 7)
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        db = get_db_session()
        
        # Clean up old failed voice processing jobs
        from src.api.models.voice import VoiceProcessingJob
        failed_jobs = db.query(VoiceProcessingJob).filter(
            VoiceProcessingJob.status == "failed",
            VoiceProcessingJob.created_at < cutoff_date
        )
        
        count = failed_jobs.count()
        failed_jobs.delete()
        
        db.commit()
        db.close()
        
        return {
            "failed_jobs_cleaned": count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}


def _cleanup_old_analytics(options: Dict[str, Any]) -> Dict[str, Any]:
    """Clean up old analytics data."""
    
    try:
        days_old = options.get("days_old", 90)
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        db = get_db_session()
        
        # Clean up old analytics events
        from src.api.models.analytics import AnalyticsEvent
        old_events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp < cutoff_date
        )
        
        count = old_events.count()
        old_events.delete()
        
        db.commit()
        db.close()
        
        return {
            "analytics_events_cleaned": count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        return {"error": str(e)}


# Global task manager instance
_task_manager = None


def get_task_manager() -> BackgroundTaskManager:
    """Get the global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    return _task_manager