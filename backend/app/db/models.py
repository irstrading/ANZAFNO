# backend/app/db/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Date, CHAR, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
Base = declarative_base()
class OptionChainSnapshot(Base):
    __tablename__ = 'option_chain_snapshots'
    time = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())
    symbol = Column(String, primary_key=True)
    expiry = Column(Date, primary_key=True)
    strike = Column(Float, primary_key=True)
    option_type = Column(CHAR(2), primary_key=True)
    ltp = Column(Float)
    oi = Column(BigInteger)
    delta = Column(Float)
    gamma = Column(Float)
class StockMetrics(Base):
    __tablename__ = 'stock_metrics'
    time = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())
    symbol = Column(String, primary_key=True)
    gex = Column(Float)
    momentum_score = Column(Float)
    verdict = Column(String)
class PriorityWatchlist(Base):
    __tablename__ = 'priority_watchlist'
    symbol = Column(String, primary_key=True)
    notes = Column(String)
    alert_config = Column(JSON)
