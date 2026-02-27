# backend/app/api/scanner.py
from fastapi import APIRouter
router = APIRouter()
@router.get("/")
async def get_scanner():
    # In production, this would fetch from Redis cache populated by Celery
    return [
        {"symbol": "RELIANCE", "score": 85, "verdict": "STRONG_BUY", "oi_signal": "LONG_BUILDUP"},
        {"symbol": "INFY", "score": 72, "verdict": "BUY_WATCH", "oi_signal": "SHORT_COVERING"}
    ]
