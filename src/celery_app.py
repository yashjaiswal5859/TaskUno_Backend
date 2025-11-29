"""
Celery application configuration.
"""
from celery import Celery
from src.config import settings

# Create Celery app
celery_app = Celery(
    "scrum_master",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.notifications.tasks.email_tasks",
        "src.notifications.tasks.notification_tasks",  # For future notifications
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result expiration
    result_expires=3600,  # 1 hour
)

# Periodic tasks (for processing email queue)
celery_app.conf.beat_schedule = {
    "process-email-queue": {
        "task": "src.notifications.tasks.email_tasks.process_email_queue",
        "schedule": 60.0,  # Run every 60 seconds
    },
}


