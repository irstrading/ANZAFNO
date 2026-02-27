# ANZA FNO Intelligence Platform - Project Details

## Overview
This platform is a high-performance, institutional-grade application for analyzing Indian F&O (Futures and Options) data. It leverages real-time data ingestion, advanced Greek calculations, and Open Interest (OI) analysis to provide actionable trading intelligence.

## Architecture
The system is designed as a modular, event-driven architecture using:
- **Backend**: Python (FastAPI) for the API layer.
- **Computation Engine**: Specialized engines for fetching, Greeks, and OI analysis.
- **Database**: PostgreSQL with TimescaleDB extension for time-series data storage.
- **Cache**: Redis for high-speed caching and pub/sub.
- **Task Queue**: Celery for background processing and periodic updates.

## Key Components

### 1. Data Fetcher Engine
- **Purpose**: Retrieves OHLC (Open, High, Low, Close), LTP (Last Traded Price), Futures, and Spot prices.
- **Sources**: Supports AngelOne SmartAPI and OpenAlgo API.
- **Features**:
  - Rate-limited fetching.
  - Automatic retry mechanism.
  - WebSocket integration for live updates.

### 2. Greeks Engine
- **Purpose**: Calculates advanced option Greeks (Delta, Gamma, Vega, Theta, Rho, Vanna, Charm).
- **Technology**: Uses `py_vollib_vectorized` for high-performance vectorized calculations.
- **Features**:
  - IV (Implied Volatility) calculation.
  - Real-time Greek updates.

### 3. OI & Analysis Engine
- **Purpose**: Analyzes Open Interest (OI) build-up and market sentiment.
- **Features**:
  - **OI Interpretation**: Identifies Long Buildup, Short Buildup, Short Covering, Long Unwinding.
  - **PCR Analysis**: Tracks Put-Call Ratio and its rate of change (Velocity).
  - **Support/Resistance**: Detects Call Walls and Put Walls.
  - **Velocity**: Measures the speed of OI changes to gauge conviction.

## Data Flow
1. **Fetch**: The Data Fetcher retrieves live market data from the broker API.
2. **Process**: The Greeks Engine computes theoretical values and risks.
3. **Analyze**: The OI Engine interprets market structure and sentiment.
4. **Store**: Processed data is stored in TimescaleDB for historical analysis.
5. **Serve**: The FastAPI backend exposes this data via REST endpoints and WebSockets to the frontend.

## Deployment
- Designed to run on Windows (localhost).
- Requires PostgreSQL (TimescaleDB) and Redis installed locally.
- Python dependencies managed via `requirements.txt`.
