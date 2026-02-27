-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create tables (handled by SQLAlchemy usually, but good to have raw SQL for reference/manual init)

-- Market Data Hypertable
CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    token TEXT NOT NULL,
    ltp DOUBLE PRECISION,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    oi BIGINT,
    atp DOUBLE PRECISION,
    PRIMARY KEY (time, symbol)
);

-- Convert to hypertable
SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);

-- Option Chain Hypertable
CREATE TABLE IF NOT EXISTS option_chain (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    expiry TIMESTAMP NOT NULL,
    strike DOUBLE PRECISION NOT NULL,

    ce_token TEXT,
    ce_ltp DOUBLE PRECISION,
    ce_oi BIGINT,
    ce_volume BIGINT,
    ce_iv DOUBLE PRECISION,
    ce_delta DOUBLE PRECISION,
    ce_gamma DOUBLE PRECISION,
    ce_vega DOUBLE PRECISION,
    ce_theta DOUBLE PRECISION,

    pe_token TEXT,
    pe_ltp DOUBLE PRECISION,
    pe_oi BIGINT,
    pe_volume BIGINT,
    pe_iv DOUBLE PRECISION,
    pe_delta DOUBLE PRECISION,
    pe_gamma DOUBLE PRECISION,
    pe_vega DOUBLE PRECISION,
    pe_theta DOUBLE PRECISION,

    PRIMARY KEY (time, symbol, expiry, strike)
);

-- Convert to hypertable
SELECT create_hypertable('option_chain', 'time', if_not_exists => TRUE);


-- Analysis Results Hypertable
CREATE TABLE IF NOT EXISTS analysis_results (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    expiry TIMESTAMP NOT NULL,

    pcr DOUBLE PRECISION,
    pcr_change DOUBLE PRECISION,
    max_pain DOUBLE PRECISION,
    call_wall DOUBLE PRECISION,
    put_wall DOUBLE PRECISION,

    sentiment TEXT,
    oi_interpretation TEXT,

    PRIMARY KEY (time, symbol, expiry)
);

-- Convert to hypertable
SELECT create_hypertable('analysis_results', 'time', if_not_exists => TRUE);

-- Instruments Table (Regular PostgreSQL table)
CREATE TABLE IF NOT EXISTS instruments (
    token TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    expiry TIMESTAMP,
    strike DOUBLE PRECISION,
    lot_size INTEGER NOT NULL,
    instrument_type TEXT NOT NULL,
    exchange TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_option_chain_symbol_expiry ON option_chain (symbol, expiry, time DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_results_symbol ON analysis_results (symbol, time DESC);
