# backend/app/api/scanner.py

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class ScannerResult(BaseModel):
    symbol: str
    momentum_score: float
    verdict_emoji: str
    oi_signal: str
    velocity_zscore: float
    gex_regime: str

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ScannerResult])
async def get_scanner_results(
    limit: int = 10,
    filter: Optional[str] = Query(None, description="bull|bear|all"),
    watchlist_only: bool = False
):
    """
    Returns top N stocks by momentum score.
    This data is pre-computed by Celery workers and stored in Redis/DB.
    """
    # Mock data for now until DB/Worker is fully integrated
    mock_data = [
        ScannerResult(
            symbol="RELIANCE",
            momentum_score=87.5,
            verdict_emoji="⚡🟢",
            oi_signal="LONG_BUILDUP",
            velocity_zscore=3.2,
            gex_regime="NEGATIVE"
        ),
        ScannerResult(
            symbol="INFY",
            momentum_score=76.0,
            verdict_emoji="🟢",
            oi_signal="SHORT_COVERING",
            velocity_zscore=1.8,
            gex_regime="POSITIVE"
        ),
        ScannerResult(
            symbol="SBIN",
            momentum_score=42.0,
            verdict_emoji="🟡",
            oi_signal="LONG_UNWINDING",
            velocity_zscore=-0.5,
            gex_regime="POSITIVE"
        ),
    ]

    return mock_data[:limit]
