"""
Celery Configuration for Financial Document Analyzer

This module configures Celery for asynchronous task processing using Redis as the message broker.
It enables concurrent processing of multiple document analysis requests.
"""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app
celery_app = Celery(
    "financial_analyzer",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["worker"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes max per task
    task_soft_time_limit=1500,  # Soft limit at 25 minutes
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
    result_expires=3600,  # Keep results for 1 hour
    broker_connection_retry_on_startup=True,
)

# Task routes (if you want to route specific tasks to specific queues)
celery_app.conf.task_routes = {
    "worker.analyze_document_task": {"queue": "financial_analysis"},
}

if __name__ == "__main__":
    celery_app.start()
