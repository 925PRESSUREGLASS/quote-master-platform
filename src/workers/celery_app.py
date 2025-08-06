"""
Celery application configuration for Quote Master Pro
"""

from celery import Celery
import os
from kombu import Queue

# Create Celery instance
celery_app = Celery("quote_master_pro")

# Configure Celery
celery_app.conf.update(
    broker_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    task_routes={
        'src.workers.background_tasks.process_voice_recording': {'queue': 'voice_processing'},
        'src.workers.background_tasks.generate_quote_ai': {'queue': 'ai_generation'},
        'src.workers.background_tasks.analyze_quote_sentiment': {'queue': 'analytics'},
        'src.workers.background_tasks.cleanup_old_recordings': {'queue': 'maintenance'},
    },
    task_default_queue='default',
    task_queues=(
        Queue('default'),
        Queue('voice_processing'),
        Queue('ai_generation'),
        Queue('analytics'),
        Queue('maintenance'),
    ),
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['src.workers'])

if __name__ == '__main__':
    celery_app.start()
