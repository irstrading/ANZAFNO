# backend/app/api/stock.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

router = APIRouter()

class StockAnalysis(BaseModel):
    symbol: str
    price: float
    oi_signal: str
    greeks: Dict[str, float]
    gex_data: Dict[str, float]
    velocity_zscore: float
    verdict: Dict[str, Any]
    structures: List[Dict[str, Any]]

    class Config:
        from_attributes = True

@router.get("/{symbol}/snapshot", response_model=StockAnalysis)
async def get_stock_snapshot(symbol: str):
    """
    Full intelligence snapshot for a single stock.
    Typically fetched from Redis cache (updated every 3min).
    """
    symbol = symbol.upper()

    # Mock data structure matching our engines
    return {
        "symbol": symbol,
        "price": 2845.50,
        "oi_signal": "LONG_BUILDUP",
        "greeks": {
            "delta": 0.52, "gamma": 0.003, "vega": 12.5, "theta": -4.2
        },
        "gex_data": {
            "gex": -25000000.0, "dex": 150000.0, "vex": -50000.0, "cex": 12000.0
        },
        "velocity_zscore": 3.1,
        "verdict": {
            "verdict": "STRONG_BUY",
            "confidence_pct": 85,
            "entry_type": "BULL CALL SPREAD",
            "key_reasons": ["High OI Velocity", "Negative GEX", "Long Buildup"]
        },
        "structures": [
            {
                "structure": "BULL_CALL_SPREAD",
                "explanation": "Buying 2840 CE / Selling 2860 CE",
                "confidence": 0.8
            }
        ]
    }

@router.get("/{symbol}/greeks")
async def get_greeks_by_strike(symbol: str):
    """
    Returns full option chain with Black-76 greeks per strike.
    """
    return [
        {"strike": 2800, "ce_delta": 0.85, "pe_delta": -0.15, "gamma": 0.001},
        {"strike": 2820, "ce_delta": 0.65, "pe_delta": -0.35, "gamma": 0.002},
        {"strike": 2840, "ce_delta": 0.52, "pe_delta": -0.48, "gamma": 0.003}, # ATM
        {"strike": 2860, "ce_delta": 0.35, "pe_delta": -0.65, "gamma": 0.002},
    ]
