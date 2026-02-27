from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "anza_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Load tasks
celery_app.autodiscover_tasks(["app.tasks"])
