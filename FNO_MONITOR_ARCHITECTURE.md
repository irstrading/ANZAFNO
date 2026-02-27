# 🔥 INDIA FNO SMART FLOW MONITOR — COMPLETE ARCHITECTURE BLUEPRINT
## Advanced Options Intelligence Platform for 150+ NSE F&O Stocks

---

## 🧠 PHILOSOPHY & CORE EDGE

> **Goal**: Catch momentum setups (intraday → 4-5 day swing) BEFORE they explode, by tracking how Smart Money (institutions, prop desks, FIIs) position via options.

The platform combines **dealer exposure mechanics** (GEX/DEX/VEX/CEX) + **OI flow signals** + **technicals** to answer one question:
> *"Which stock has institutional accumulation happening RIGHT NOW in the options market, and is about to make a directional move?"*

---

## 📐 SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                          │
│  NSE API → nsepython / nsefin / Broker APIs (Fyers/Upstox)     │
│  → Redis Queue → Raw Option Chain Store (TimescaleDB/PostgreSQL) │
└─────────────────────┬───────────────────────────────────────────┘
                      │ Every 3-5 min (market hours)
┌─────────────────────▼───────────────────────────────────────────┐
│                  COMPUTATION ENGINE (Python)                     │
│  Greeks Engine → OI Analysis → Flow Scoring → Signal Generator  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                     API LAYER (FastAPI)                          │
│      WebSocket (live) + REST endpoints + Alert Engine           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│               FRONTEND DASHBOARD (React + Recharts)             │
│    Scanner → Stock Drill-Down → OI Charts → Greek Heatmaps      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ TECH STACK

### Backend
- **Language**: Python 3.11+
- **Web Framework**: FastAPI (async, WebSocket support)
- **Task Queue**: Celery + Redis (data fetching, computation scheduling)
- **Database**:
  - **TimescaleDB** (PostgreSQL extension) → time-series OI/price data
  - **Redis** → real-time cache, pub/sub for WebSockets
  - **SQLite** → config, watchlists, alerts
- **Greeks Computation**: `py_vollib`, `mibian`, or custom Black-76 (for Indian index options)
- **Data Libraries**: `nsepython`, `nsefin`, `pandas`, `numpy`, `scipy`

### Frontend
- **React 18** + **Vite**
- **Charting**: Recharts + D3.js (for heatmaps)
- **State**: Zustand or Redux Toolkit
- **Real-time**: Native WebSocket client
- **UI**: Custom dark-theme CSS (no Bootstrap)

### Data Sources
| Source | What | How |
|--------|------|-----|
| NSE India API | Live option chain, OI, IV | `nsepython` / direct HTTP |
| NSE Bhavcopy | EOD OI, futures data | `nsefin.get_fno_bhav_copy()` |
| Broker API (Fyers/Upstox) | Real-time LTP, futures OI | Websocket subscription |
| NSE FII/DII data | Participant-wise OI | NSE website scrape |

---

## 📊 MODULE 1: OI ANALYSIS ENGINE

### OI Interpretation Matrix
```
Price ↑ + OI ↑  = LONG BUILDUP     → Bullish 🟢
Price ↓ + OI ↑  = SHORT BUILDUP    → Bearish 🔴
Price ↑ + OI ↓  = SHORT COVERING   → Bullish but weak 🟡
Price ↓ + OI ↓  = LONG UNWINDING   → Bearish but weak 🟠
```

### Key OI Metrics to Compute (Per Stock, Per Strike, Per Expiry)

```python
# For each FNO stock every 3-5 minutes:

class OISnapshot:
    # Raw
    call_oi: dict[strike, int]
    put_oi: dict[strike, int]
    call_oi_change: dict[strike, int]     # vs prev snapshot
    put_oi_change: dict[strike, int]
    call_volume: dict[strike, int]
    put_volume: dict[strike, int]
    futures_oi: int
    futures_oi_change: int
    
    # Derived
    pcr_oi: float                          # Total Put OI / Total Call OI
    pcr_volume: float
    max_pain: float                        # Strike where writers lose least
    max_call_oi_strike: float              # Resistance level
    max_put_oi_strike: float               # Support level
    
    # Change-based
    net_call_addition: int                 # Fresh call writes (bearish)
    net_put_addition: int                  # Fresh put writes (bullish)
    oi_buildup_signal: str                 # Long/Short/Covering/Unwinding
    
    # Cumulative OI Change (COIC) — very powerful
    cumulative_call_change_today: int
    cumulative_put_change_today: int
    
    # Volume/OI ratio — detects unsual activity
    call_vol_oi_ratio: float               # >0.5 = unusual activity
    put_vol_oi_ratio: float
```

### Max Pain Calculation
```python
def calculate_max_pain(option_chain: pd.DataFrame, spot: float) -> float:
    strikes = option_chain['strike'].unique()
    pain = {}
    for expiry_price in strikes:
        total_pain = 0
        for strike in strikes:
            call_oi = option_chain.loc[option_chain['strike']==strike, 'call_oi'].sum()
            put_oi = option_chain.loc[option_chain['strike']==strike, 'put_oi'].sum()
            call_pain = max(0, expiry_price - strike) * call_oi * 100
            put_pain = max(0, strike - expiry_price) * put_oi * 100
            total_pain += call_pain + put_pain
        pain[expiry_price] = total_pain
    return min(pain, key=pain.get)
```

---

## 📊 MODULE 2: ADVANCED GREEKS ENGINE

### Black-76 Model for Indian Options
Indian index/stock options are **European style**, best priced with Black-76 or BSM.

```python
from scipy.stats import norm
import numpy as np

class GreeksEngine:
    """
    Computes all greeks for Indian FNO options using Black-76
    """
    
    def black76(self, F, K, T, r, sigma, option_type):
        """F=Futures price, K=Strike, T=Time to expiry (years)"""
        d1 = (np.log(F/K) + 0.5*sigma**2*T) / (sigma*np.sqrt(T))
        d2 = d1 - sigma*np.sqrt(T)
        if option_type == 'CE':
            price = np.exp(-r*T) * (F*norm.cdf(d1) - K*norm.cdf(d2))
            delta = np.exp(-r*T) * norm.cdf(d1)
        else:
            price = np.exp(-r*T) * (K*norm.cdf(-d2) - F*norm.cdf(-d1))
            delta = -np.exp(-r*T) * norm.cdf(-d1)
        
        gamma = np.exp(-r*T) * norm.pdf(d1) / (F * sigma * np.sqrt(T))
        vega = F * np.exp(-r*T) * norm.pdf(d1) * np.sqrt(T) / 100
        theta = (-F*np.exp(-r*T)*norm.pdf(d1)*sigma/(2*np.sqrt(T)) 
                 - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365
        
        # Second-order greeks
        vanna = -np.exp(-r*T) * norm.pdf(d1) * d2 / sigma
        charm = -np.exp(-r*T) * (norm.pdf(d1) * (r/(sigma*np.sqrt(T)) - d2/(2*T)))
        
        return {
            'delta': delta, 'gamma': gamma, 'vega': vega,
            'theta': theta, 'vanna': vanna, 'charm': charm
        }
```

### Dealer Exposure Calculations

```python
class DealerExposure:
    """
    Assumes market makers are counterparty to all trades.
    Dealers BUY calls when retail SELLS, and SELL puts when retail BUYS.
    Hedge direction is opposite of their book.
    """
    
    def compute_gex(self, option_chain: pd.DataFrame, spot: float) -> float:
        """
        GEX = Γ * OI * spot² * 0.01
        Positive GEX: Dealers long gamma → stabilize price (sell rips, buy dips)
        Negative GEX: Dealers short gamma → amplify moves (DANGER ZONE)
        """
        gex = 0
        for _, row in option_chain.iterrows():
            gamma = row['gamma']
            oi = row['oi']
            lot_size = row['lot_size']
            # Calls: dealers are short → negative contribution
            # Puts: dealers are long puts → positive contribution
            sign = 1 if row['option_type'] == 'PE' else -1
            gex += sign * gamma * oi * lot_size * (spot**2) * 0.01
        return gex
    
    def compute_dex(self, option_chain: pd.DataFrame) -> float:
        """
        DEX = Δ * OI * lot_size
        Directional pressure dealers must hedge
        """
        dex = 0
        for _, row in option_chain.iterrows():
            sign = -1 if row['option_type'] == 'CE' else 1
            dex += sign * row['delta'] * row['oi'] * row['lot_size']
        return dex
    
    def compute_vex(self, option_chain: pd.DataFrame, spot: float) -> float:
        """
        VEX = Vanna * OI * lot_size * spot * IV
        Tells you: if IV drops, which direction dealers must hedge?
        Critical around earnings, events, RBI policy
        """
        vex = 0
        for _, row in option_chain.iterrows():
            sign = -1 if row['option_type'] == 'CE' else 1
            vex += sign * row['vanna'] * row['oi'] * row['lot_size'] * spot * row['iv']
        return vex
    
    def compute_cex(self, option_chain: pd.DataFrame) -> float:
        """
        CEX = Charm * OI * lot_size
        Time-decay driven hedging — peaks Thursday/Friday near expiry
        Critical insight: "charm bleed" near expiry can cause directional drift
        """
        cex = 0
        for _, row in option_chain.iterrows():
            sign = -1 if row['option_type'] == 'CE' else 1
            cex += sign * row['charm'] * row['oi'] * row['lot_size']
        return cex
    
    def gex_flip_level(self, option_chain: pd.DataFrame) -> float:
        """
        Strike where GEX changes sign = zero gamma level
        Below this: negative gamma → explosive moves likely
        Above this: positive gamma → compression/pinning
        """
        # Find strike where cumulative GEX crosses zero
        ...
```

---

## 📊 MODULE 3: SMART MONEY FLOW DETECTOR

### FII/DII Participant OI Tracking
NSE publishes participant-wise OI daily — track FII net position changes:
```
FII Net Long F&O = (FII Index Long + Stock Long) - (FII Index Short + Stock Short)
If FII adding longs + price rising = STRONG BULLISH
If FII adding shorts + price falling = STRONG BEARISH
```

### Unusual Options Activity (UOA) Detection
```python
def detect_unusual_activity(snapshot: OISnapshot) -> dict:
    signals = []
    
    # 1. Volume/OI Spike — fresh money, not closing
    for strike in snapshot.strikes:
        vol_oi_ratio = snapshot.call_volume[strike] / max(snapshot.call_oi[strike], 1)
        if vol_oi_ratio > 0.5 and snapshot.call_oi_change[strike] > 0:
            signals.append({
                'type': 'UNUSUAL_CALL_VOLUME',
                'strike': strike,
                'ratio': vol_oi_ratio,
                'interpretation': 'Fresh call buying — Bullish'
            })
    
    # 2. Aggressive OTM Buying
    atm_strike = get_atm_strike(snapshot.spot)
    for strike in snapshot.call_strikes:
        if strike > atm_strike * 1.05:   # >5% OTM
            if snapshot.call_oi_change[strike] > snapshot.avg_call_oi_change * 3:
                signals.append({
                    'type': 'OTM_CALL_ACCUMULATION',
                    'strike': strike,
                    'urgency': 'HIGH',
                    'interpretation': 'Smart money buying OTM calls — expects big move up'
                })
    
    # 3. Put-Call OI Ratio extremes
    pcr = snapshot.pcr_oi
    if pcr > 1.6:    # Oversold / reversal signal
        signals.append({'type': 'PCR_EXTREME_HIGH', 'pcr': pcr, 'bias': 'CONTRARIAN_BULLISH'})
    elif pcr < 0.5:  # Overbought / reversal signal
        signals.append({'type': 'PCR_EXTREME_LOW', 'pcr': pcr, 'bias': 'CONTRARIAN_BEARISH'})
    
    # 4. Gamma Squeeze Setup
    # When negative GEX is extreme, any breakout is amplified by dealer covering
    if snapshot.gex < -50_000_000:   # Tune threshold per stock
        signals.append({'type': 'NEGATIVE_GAMMA_ZONE', 'gex': snapshot.gex,
                        'interpretation': 'Any breakout will be explosive — dealers will amplify'})
    
    return signals
```

### Call Wall / Put Wall Detection
```python
def get_key_levels(option_chain: pd.DataFrame) -> dict:
    return {
        'call_wall': option_chain.groupby('strike')['call_oi'].sum().idxmax(),  # Resistance
        'put_wall': option_chain.groupby('strike')['put_oi'].sum().idxmax(),    # Support
        'max_pain': calculate_max_pain(option_chain),
        'gex_zero_level': find_gex_flip(option_chain),                          # Key: gamma flip
        'high_vex_strikes': find_vex_concentration(option_chain),               # IV event levels
    }
```

---

## 📊 MODULE 4: STOCK SCORING & RANKING ENGINE

### Composite Momentum Score (0–100)

```python
def compute_momentum_score(stock: str, data: StockData) -> float:
    score = 0
    weights = {
        'oi_signal': 25,        # OI buildup type
        'gex_regime': 20,       # Negative GEX = explosive potential
        'unusual_flow': 20,     # UOA — smart money
        'fii_positioning': 15,  # FII net delta
        'technicals': 20,       # RSI, MACD, volume, breakout
    }
    
    # 1. OI Signal Score
    if data.oi_signal == 'LONG_BUILDUP':         score += 25
    elif data.oi_signal == 'SHORT_COVERING':      score += 15
    elif data.oi_signal == 'SHORT_BUILDUP':       score -= 10
    
    # 2. GEX Regime
    if data.gex < 0:    # Negative gamma = explosive zone
        score += min(20, abs(data.gex) / 1_000_000 * 5)
    
    # 3. Unusual Flow
    uoa = data.unusual_activity
    score += len([x for x in uoa if x['urgency'] == 'HIGH']) * 8
    score += len([x for x in uoa if x['urgency'] == 'MEDIUM']) * 4
    
    # 4. FII Net Delta contribution
    if data.fii_net_delta_change > 0:
        score += min(15, data.fii_net_delta_change / 10_000 * 5)
    
    # 5. Technicals
    if data.rsi_14 < 40:       score += 10   # Oversold + buildup = strong
    if data.macd_crossover:    score += 5
    if data.vol_spike:         score += 5    # Volume >2x avg
    if data.breakout:          score += 5    # Price > key resistance
    
    return min(100, max(0, score))
```

### Multi-Timeframe OI Trend
```
Per stock, track OI change at:
- 5min  → intraday scalp signals
- 30min → momentum confirmation
- EOD   → swing trade setup (4-5 day)
- Weekly rollover → positional trend
```

---

## 📊 MODULE 5: TECHNICAL ANALYSIS LAYER

### Indicators Computed Per Stock
```python
TECHNICAL_SIGNALS = {
    'trend': ['EMA_9', 'EMA_21', 'EMA_50', 'VWAP'],
    'momentum': ['RSI_14', 'MACD', 'Stochastic'],
    'volatility': ['ATR_14', 'Bollinger_Bands', 'IV_Rank', 'IV_Percentile'],
    'volume': ['OBV', 'VWAP_deviation', 'Relative_Volume'],
    'structure': ['Support_Resistance', 'Pivot_Points', 'Max_Pain_Distance'],
}
```

### IV Rank & IV Percentile (Key for timing entries)
```python
def iv_rank(current_iv: float, iv_history_1yr: list) -> float:
    """IV Rank: 0–100. High = options expensive. Low = options cheap."""
    low, high = min(iv_history_1yr), max(iv_history_1yr)
    return (current_iv - low) / (high - low) * 100

def iv_percentile(current_iv: float, iv_history_1yr: list) -> float:
    """% of days IV was below current level"""
    return sum(1 for iv in iv_history_1yr if iv < current_iv) / len(iv_history_1yr) * 100
```

---

## 🗄️ DATABASE SCHEMA

### TimescaleDB Tables

```sql
-- Option chain snapshots (hypertable partitioned by time)
CREATE TABLE option_chain_snapshots (
    time         TIMESTAMPTZ NOT NULL,
    symbol       TEXT NOT NULL,
    expiry       DATE NOT NULL,
    strike       NUMERIC NOT NULL,
    option_type  CHAR(2) NOT NULL,   -- CE/PE
    ltp          NUMERIC,
    iv           NUMERIC,
    oi           BIGINT,
    oi_change    BIGINT,
    volume       BIGINT,
    delta        NUMERIC,
    gamma        NUMERIC,
    theta        NUMERIC,
    vega         NUMERIC,
    vanna        NUMERIC,
    charm        NUMERIC
);
SELECT create_hypertable('option_chain_snapshots', 'time');

-- Derived metrics per stock per snapshot
CREATE TABLE stock_metrics (
    time              TIMESTAMPTZ NOT NULL,
    symbol            TEXT NOT NULL,
    spot_price        NUMERIC,
    futures_oi        BIGINT,
    futures_oi_change BIGINT,
    pcr_oi            NUMERIC,
    pcr_volume        NUMERIC,
    max_pain          NUMERIC,
    call_wall         NUMERIC,
    put_wall          NUMERIC,
    gex               NUMERIC,
    dex               NUMERIC,
    vex               NUMERIC,
    cex               NUMERIC,
    oi_signal         TEXT,
    momentum_score    NUMERIC,
    fii_net_delta     BIGINT
);
SELECT create_hypertable('stock_metrics', 'time');
```

---

## 🌐 API DESIGN (FastAPI)

### REST Endpoints
```
GET /api/scanner                    → Top 10 stocks by momentum score (refreshes every 3min)
GET /api/stock/{symbol}/snapshot    → Latest all metrics for one stock
GET /api/stock/{symbol}/oi-history  → OI time series for charts
GET /api/stock/{symbol}/greeks      → GEX/DEX/VEX/CEX by strike
GET /api/stock/{symbol}/levels      → Call wall, put wall, max pain, GEX flip
GET /api/market/overview            → Market-wide GEX, Nifty PCR, FII data
GET /api/alerts                     → Active alert conditions triggered
```

### WebSocket Endpoints
```
WS /ws/scanner          → Pushes updated scanner every 3min
WS /ws/stock/{symbol}   → Live OI/price stream for a specific stock
WS /ws/alerts           → Real-time alert notifications
```

---

## 🖥️ FRONTEND DASHBOARD PAGES

### Page 1: Smart Scanner (Main Dashboard)
```
┌─────────────────────────────────────────────────────────┐
│  INDIA FNO FLOW MONITOR    [Market Regime: -GEX ⚠️]     │
│  Nifty: 23,450 ▲ | BN: 49,200 ▲ | VIX: 14.2 ▼ | Live │
├──────────┬──────────┬───────┬──────┬───────┬────────────┤
│ SYMBOL   │ SCORE    │ OI    │ GEX  │ FLOW  │ SIGNAL     │
├──────────┼──────────┼───────┼──────┼───────┼────────────┤
│ RELIANCE │ 87 🔥    │ Long↑ │ -VE  │ UOA✅ │ BREAKOUT   │
│ INFY     │ 76 🟢    │ SC ↑  │ +VE  │ FII✅ │ MOMENTUM   │
│ TATASTEEL│ 71 🟢    │ Long↑ │ -VE  │ OTM✅ │ WATCHLIST  │
└──────────┴──────────┴───────┴──────┴───────┴────────────┘
```

### Page 2: Stock Drill-Down
- **OI by Strike Chart** (bar, color coded call/put)
- **OI Change Over Time** (heatmap — time vs strike)
- **GEX by Strike** (waterfall chart)
- **DEX / VEX / CEX** panels
- **Price + VWAP + Volume** chart
- **Dealer Exposure Summary** card
- **Smart Money Signals** list

### Page 3: OI Time Machine
- Replay OI snapshots from open to current
- See exactly WHERE and WHEN smart money positioned

### Page 4: Greek Exposure Heatmap
- All 150 FNO stocks on one grid
- Color = GEX regime (green=positive/stable, red=negative/explosive)
- Size = momentum score

### Page 5: Alerts Center
- Configurable: "Alert me when GEXFLIP on RELIANCE"
- "Alert on PCR < 0.5 for NIFTY"
- "Alert when OTM Call accumulation > 3x avg"

---

## ⏱️ DATA FLOW & TIMING

```
09:00 IST  Pre-market: Fetch overnight OI from bhavcopy, compute base levels
09:15 IST  Market open: Start live option chain polling (every 3 min)
09:15-15:30  Continuous:
    → Poll NSE option chain per symbol batch
    → Compute greeks via Black-76
    → Compute GEX/DEX/VEX/CEX
    → Update OI signals (buildup/covering/unwinding)
    → Compute momentum score
    → Push to WebSocket clients
    → Check alert conditions
15:30 IST  EOD: Store daily OI summary, compute IV percentile, FII data
```

### Batch Processing (150 stocks × every 3 min)
- **Strategy**: Group 150 stocks into 5 batches of 30, stagger with 30s delay
- **Rate Limit**: NSE rate limits aggressively — use exponential backoff
- **Caching**: Store in Redis for sub-second frontend reads
- **Parallel**: Use `asyncio.gather()` for concurrent fetching

---

## 🔔 SIGNAL LIBRARY (Triggers for Alerts)

| Signal | Condition | Timeframe |
|--------|-----------|-----------|
| `LONG_BUILDUP` | Price↑ + OI↑ + Futures OI↑ | Intraday/Swing |
| `SHORT_SQUEEZE_SETUP` | High short OI + price resistance break + vol spike | Intraday |
| `GAMMA_FLIP` | GEX crosses zero → explosive zone entered | Intraday |
| `OTM_ACCUMULATION` | OTM call OI added >3x avg in <30min | Intraday |
| `CHARM_BLEED_BULL` | CEX positive + near expiry + put OI unwinding | Expiry day |
| `VANNA_FUEL_BULL` | VEX negative + IV compression expected | Event-based |
| `MAX_PAIN_MAGNET` | Price >5% above/below max pain near expiry | Expiry week |
| `FII_NET_LONG_SURGE` | FII adds >10K net longs in futures | EOD/overnight |
| `PCR_REVERSAL` | PCR crosses above 1.5 (buy) or below 0.6 (sell) | Intraday |
| `IV_CRUSH_SETUP` | IV rank >80 + event tomorrow | Pre-event |
| `DELTA_HEDGING_PRESSURE` | DEX extreme → forced buying/selling incoming | Intraday |

---

## 🚀 DEVELOPMENT ROADMAP

### Phase 1 — Core (Week 1-2)
- [ ] Data ingestion: NSE option chain poller for all 150 FNO stocks
- [ ] Greeks engine: Black-76 delta, gamma, vega, theta, vanna, charm
- [ ] OI signal computation (buildup/covering/unwinding)
- [ ] TimescaleDB schema + FastAPI skeleton
- [ ] Basic scanner table in React

### Phase 2 — Intelligence (Week 3-4)
- [ ] GEX/DEX/VEX/CEX dealer exposure engine
- [ ] Momentum scoring system
- [ ] Unusual activity detector
- [ ] Max pain, call wall, put wall, GEX flip level computation
- [ ] WebSocket live push

### Phase 3 — Visualization (Week 5-6)
- [ ] OI by strike bar chart (live updating)
- [ ] OI change heatmap (time × strike)
- [ ] GEX waterfall chart per stock
- [ ] Greek exposure heatmap (all 150 stocks)
- [ ] Stock drill-down page

### Phase 4 — Advanced (Week 7-8)
- [ ] Alert engine (push/email/Telegram)
- [ ] FII/DII participant tracking
- [ ] IV Rank/Percentile engine
- [ ] OI Time Machine (replay)
- [ ] Technical overlays (VWAP, EMA, volume)

### Phase 5 — Production (Week 9-10)
- [ ] Rate limiting + proxy rotation for NSE
- [ ] Auth (login, watchlists saved per user)
- [ ] Mobile responsive
- [ ] Backtesting: did signals work historically?
- [ ] Docker Compose for one-command setup

---

## 📁 PROJECT DIRECTORY STRUCTURE

```
fno-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app
│   │   ├── api/
│   │   │   ├── scanner.py        # Scanner endpoints
│   │   │   ├── stock.py          # Stock drill-down
│   │   │   └── websocket.py      # WS handlers
│   │   ├── core/
│   │   │   ├── greeks.py         # Black-76 engine
│   │   │   ├── oi_analysis.py    # OI signals
│   │   │   ├── dealer_exposure.py # GEX/DEX/VEX/CEX
│   │   │   ├── scoring.py        # Momentum score
│   │   │   └── signals.py        # Alert signals
│   │   ├── data/
│   │   │   ├── nse_fetcher.py    # NSE API client
│   │   │   ├── fii_tracker.py    # FII/DII data
│   │   │   └── fno_stocks.py     # 150 FNO stock list
│   │   ├── db/
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   └── timescale.py      # TimescaleDB queries
│   │   └── tasks/
│   │       ├── celery_app.py     # Celery config
│   │       └── polling_tasks.py  # Data fetch tasks
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Scanner.jsx       # Main scanner
│   │   │   ├── StockView.jsx     # Drill-down
│   │   │   ├── Heatmap.jsx       # All stocks GEX
│   │   │   └── Alerts.jsx
│   │   ├── components/
│   │   │   ├── OIChart.jsx       # OI by strike
│   │   │   ├── GEXWaterfall.jsx  # GEX chart
│   │   │   ├── OIHeatmap.jsx     # Time × strike
│   │   │   ├── DealerPanel.jsx   # GEX/DEX/VEX/CEX
│   │   │   └── ScoreCard.jsx     # Momentum score
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js
│   │   │   └── useStockData.js
│   │   └── store/
│   │       └── index.js          # Zustand store
│   └── package.json
├── docker-compose.yml            # One-command start
└── README.md
```

---

## ⚠️ KNOWN CHALLENGES & SOLUTIONS

| Challenge | Solution |
|-----------|----------|
| NSE rate limiting / 403 errors | Randomize User-Agent, add delays, use session cookies |
| Greeks accuracy for Indian stocks | Use Black-76 (not BSM) for index options; BSM for stocks |
| 150 stocks × 3min refresh = heavy load | Batch + async; prioritize watchlist stocks first |
| NSE API changes frequently | Abstract fetcher; fallback to `nsepython`/`nsefin` |
| Historical OI for backtesting | Use NSE bhavcopy EOD data; store intraday snapshots |
| Lot size changes | Maintain lot size table updated monthly |

---

## 📚 KEY REFERENCES & RESOURCES

### Greek Exposure Theory
- SpotGamma methodology (GEX pioneer)
- VannaCharm by Chris Frewin (Medium) — VEX/CEX calculations
- Unusual Whales Greek Exposure educational series

### India-Specific
- `nsepython` PyPI — NSE API wrapper
- `nsefin` PyPI — FNO bhavcopy and option chain
- `VarunS2002/Python-NSE-Option-Chain-Analyzer` GitHub — OI analysis reference
- NSE Participant-wise OI: niftytrader.in

### Academic / Deep Theory
- Black-Scholes-Merton (1973) original paper
- Black (1976) — Futures options pricing (Indian index options)
- "Volatility Surface" by Gatheral — IV dynamics
- Carr & Madan — Variance swaps and realized vol

---

*Built for Indian F&O traders. Use responsibly. Not financial advice.*
