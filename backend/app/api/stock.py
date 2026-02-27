# backend/app/api/stock.py
from fastapi import APIRouter
router = APIRouter()
@router.get("/{symbol}")
async def get_stock(symbol: str): return {"symbol": symbol}
