# backend/app/tasks/celery_app.py

from celery import Celery
from ..config import settings

celery_app = Celery(
    "anza_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Example scheduled task configuration (beat)
celery_app.conf.beat_schedule = {
    # 'scan-watchlist-every-minute': {
    #     'task': 'app.tasks.scan_tasks.scan_watchlist',
    #     'schedule': 60.0,
    # },
}

@celery_app.task
def dummy_task():
    return "Celery is working!"
