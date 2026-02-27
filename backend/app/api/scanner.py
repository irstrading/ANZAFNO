from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.market import AnalysisResult, OptionChain
from app.engine.manager import MarketDataManager

router = APIRouter()
manager = MarketDataManager()

@router.get("/overview", response_model=dict)
async def get_market_overview(db: Session = Depends(get_db)):
    """
    Get high-level market overview: NIFTY/BANKNIFTY PCR, Max Pain, Sentiment.
    """
    # Fetch latest analysis results from DB
    nifty = db.query(AnalysisResult).filter(AnalysisResult.symbol == "NIFTY").order_by(AnalysisResult.time.desc()).first()
    banknifty = db.query(AnalysisResult).filter(AnalysisResult.symbol == "BANKNIFTY").order_by(AnalysisResult.time.desc()).first()

    return {
        "nifty": nifty,
        "banknifty": banknifty,
        "timestamp": nifty.time if nifty else None
    }

@router.get("/option-chain/{symbol}", response_model=List[dict])
async def get_option_chain(symbol: str, db: Session = Depends(get_db)):
    """
    Get processed Option Chain with Greeks for a symbol.
    """
    # Fetch latest option chain snapshot
    chain = db.query(OptionChain).filter(OptionChain.symbol == symbol).order_by(OptionChain.time.desc()).limit(100).all()
    if not chain:
        raise HTTPException(status_code=404, detail="Option Chain not found")

    return chain

@router.get("/analysis/{symbol}", response_model=dict)
async def get_analysis(symbol: str, db: Session = Depends(get_db)):
    """
    Get detailed OI analysis (PCR, Walls, Max Pain) for a symbol.
    """
    analysis = db.query(AnalysisResult).filter(AnalysisResult.symbol == symbol).order_by(AnalysisResult.time.desc()).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis
