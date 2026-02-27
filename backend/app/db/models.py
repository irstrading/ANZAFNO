# backend/app/db/models.py

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, BigInteger, Numeric, Index, text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class OptionChainSnapshot(Base):
    __tablename__ = "option_chain_snapshots"

    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    symbol = Column(String, primary_key=True, index=True)
    expiry = Column(DateTime)
    strike = Column(Numeric, primary_key=True)
    option_type = Column(String(2), primary_key=True) # CE/PE

    ltp = Column(Numeric)
    iv = Column(Numeric)
    oi = Column(BigInteger)
    oi_change = Column(BigInteger)
    volume = Column(BigInteger)

    delta = Column(Numeric)
    gamma = Column(Numeric)
    theta = Column(Numeric)
    vega = Column(Numeric)
    vanna = Column(Numeric)
    charm = Column(Numeric)

class StockMetric(Base):
    __tablename__ = "stock_metrics"

    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    symbol = Column(String, primary_key=True, index=True)

    spot_price = Column(Numeric)
    futures_oi = Column(BigInteger)
    futures_oi_change = Column(BigInteger)

    pcr_oi = Column(Numeric)
    pcr_volume = Column(Numeric)
    max_pain = Column(Numeric)
    call_wall = Column(Numeric)
    put_wall = Column(Numeric)

    gex = Column(Numeric)
    dex = Column(Numeric)
    vex = Column(Numeric)
    cex = Column(Numeric)

    oi_signal = Column(String)
    momentum_score = Column(Numeric)
    fii_net_delta = Column(BigInteger)

class StructureDetectionLog(Base):
    __tablename__ = "structure_detections"

    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    symbol = Column(String, index=True)
    structure_type = Column(String)
    confidence = Column(Numeric)
    buy_leg_strike = Column(Numeric, nullable=True)
    sell_leg_strike = Column(Numeric, nullable=True)
    net_premium = Column(String) # DEBIT/CREDIT
    directional_bias = Column(String)
    conviction = Column(String)
    explanation = Column(String)

class SmartMoneyVerdictLog(Base):
    __tablename__ = "smart_money_verdicts"

    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    symbol = Column(String, index=True)
    verdict = Column(String)
    confidence_pct = Column(Integer)
    holding_period = Column(String)
    entry_type = Column(String)
    entry_strike = Column(Numeric, nullable=True)
    stop_loss = Column(Numeric)
    target_pct = Column(Numeric)
    key_reasons = Column(JSON)
    red_flags = Column(JSON)

class OIVelocityLog(Base):
    __tablename__ = "oi_velocity_log"

    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    symbol = Column(String, index=True)
    strike = Column(Numeric)
    option_type = Column(String(2))

    velocity_3min = Column(Numeric)
    velocity_15min = Column(Numeric)
    velocity_30min = Column(Numeric)
    velocity_zscore = Column(Numeric)
    acceleration = Column(Numeric)
    vol_oi_ratio = Column(Numeric)
    freshness_class = Column(String)

class TelegramAlertSent(Base):
    __tablename__ = "telegram_alerts_sent"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    symbol = Column(String)
    signal_type = Column(String)
    priority = Column(String)
    verdict = Column(String)
    message_preview = Column(String)
