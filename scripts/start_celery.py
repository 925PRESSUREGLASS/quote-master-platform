"""
Start Celery worker for Quote Master Pro
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workers.celery_app import celery_app

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Start the worker
    celery_app.worker_main(['worker', '--loglevel=info', '--concurrency=2'])
