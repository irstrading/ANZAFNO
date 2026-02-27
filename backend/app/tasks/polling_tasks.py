# backend/app/tasks/polling_tasks.py
from app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def scan_watchlist():
    logger.info("Scanning watchlist...")
    # Real logic would fetch from DB, then API, then compute & save
    return {"status": "success"}

@celery_app.task
def scan_all_fno():
    logger.info("Scanning all F&O...")
    return {"status": "success"}
