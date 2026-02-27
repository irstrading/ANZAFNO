# backend/app/tasks/celery_app.py
import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "anza_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "scan-watchlist-every-minute": {
        "task": "app.tasks.polling_tasks.scan_watchlist",
        "schedule": 60.0,
    },
    "scan-all-fno-every-3-minutes": {
        "task": "app.tasks.polling_tasks.scan_all_fno",
        "schedule": 180.0,
    },
}

import app.tasks.polling_tasks # Ensure tasks are registered
