from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.db.session import Base

class Instrument(Base):
    __tablename__ = "instruments"

    token = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    expiry = Column(DateTime, nullable=True)
    strike = Column(Float, nullable=True)
    lot_size = Column(Integer, nullable=False)
    instrument_type = Column(String, nullable=False)  # FUT, CE, PE, EQ
    exchange = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())

class MarketData(Base):
    __tablename__ = "market_data"

    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    symbol = Column(String, primary_key=True, index=True)
    token = Column(String, nullable=False)
    ltp = Column(Float, nullable=False)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)
    oi = Column(Integer, nullable=True)
    atp = Column(Float, nullable=True)

class OptionChain(Base):
    __tablename__ = "option_chain"

    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    symbol = Column(String, primary_key=True, index=True)
    expiry = Column(DateTime, primary_key=True, nullable=False)
    strike = Column(Float, primary_key=True, nullable=False)

    # Call Data
    ce_token = Column(String, nullable=True)
    ce_ltp = Column(Float, nullable=True)
    ce_oi = Column(Integer, nullable=True)
    ce_volume = Column(Integer, nullable=True)
    ce_iv = Column(Float, nullable=True)
    ce_delta = Column(Float, nullable=True)
    ce_gamma = Column(Float, nullable=True)
    ce_vega = Column(Float, nullable=True)
    ce_theta = Column(Float, nullable=True)

    # Put Data
    pe_token = Column(String, nullable=True)
    pe_ltp = Column(Float, nullable=True)
    pe_oi = Column(Integer, nullable=True)
    pe_volume = Column(Integer, nullable=True)
    pe_iv = Column(Float, nullable=True)
    pe_delta = Column(Float, nullable=True)
    pe_gamma = Column(Float, nullable=True)
    pe_vega = Column(Float, nullable=True)
    pe_theta = Column(Float, nullable=True)

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    symbol = Column(String, primary_key=True, index=True)
    expiry = Column(DateTime, primary_key=True, nullable=False)

    pcr = Column(Float, nullable=True)
    pcr_change = Column(Float, nullable=True)
    max_pain = Column(Float, nullable=True)
    call_wall = Column(Float, nullable=True)
    put_wall = Column(Float, nullable=True)

    # Sentiment
    sentiment = Column(String, nullable=True)  # BULLISH, BEARISH, NEUTRAL
    oi_interpretation = Column(String, nullable=True) # LONG_BUILDUP, SHORT_COVERING, etc.
