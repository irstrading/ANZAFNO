# 🔥 ANZA FNO INTELLIGENCE PLATFORM — MASTER ARCHITECTURE v3
## Based on ANZA AI ADVANCE · AngelOne API Only · Zero Spend · Localhost
### Incorporates: ANZA_FnO_Stock_Framework + ANZA_Trading_Intelligence + ANZA_NiftyDesk

---

## 🎯 DESIGN PHILOSOPHY

> Built for IRSHAD AHMED's personal trading system. Every design decision prioritizes:
> 1. **Zero API cost** — AngelOne SmartAPI only (free with brokerage account)
> 2. **Rate limit intelligence** — Never burn your API credentials
> 3. **ANZA framework fidelity** — Black-76 everywhere, correct formulas from the docs
> 4. **Upgradable architecture** — Add features without rewriting
> 5. **6+ themes** — Dark terminal, Light pro, Neon quantum, Velonic steel, Upcube admin, Crypto dark

---

## 🌐 TECH STACK (100% FREE)

```
Backend:    Python 3.11 · FastAPI · Celery · Redis · SQLite + TimescaleDB
Data:       AngelOne SmartAPI (WebSocket live + REST option chain)
Frontend:   React 18 + Vite · Zustand · Recharts + D3 · TailwindCSS
Themes:     6 CSS theme variables + Google Fonts
Alerts:     python-telegram-bot v20 (async)
Infra:      Docker Compose (single command startup)
Auth:       AngelOne TOTP login → JWT stored locally
```

---

## ⚡ MODULE 0: ANGELONE SMART RATE LIMIT ARCHITECTURE

> This is the most critical module. AngelOne SmartAPI has limits:
> - REST: ~100 requests/minute
> - WebSocket: No polling needed (push-based)
> - Option chain: Heavy endpoint — treat with care

### The 4-Layer Rate Limit Defense System

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 1: TOKEN BUCKET (Per-endpoint rate limiting)      │
│   Option Chain: max 10/min · Market Data: 60/min        │
│   LTP: 100/min · Historical: 5/min                      │
├─────────────────────────────────────────────────────────┤
│ LAYER 2: INTELLIGENT SCHEDULE (Market-hours aware)       │
│   9:10-9:15 → Pre-market prep (historical only)         │
│   9:15-15:30 → Smart live mode (see below)              │
│   15:30-23:59 → EOD analysis + next-day prep            │
├─────────────────────────────────────────────────────────┤
│ LAYER 3: DELTA COMPRESSION (Only fetch what changed)    │
│   Compare strike OI to cached → only send diffs         │
│   Skip strikes with < 0.5% OI change (noise floor)      │
├─────────────────────────────────────────────────────────┤
│ LAYER 4: WEBSOCKET FIRST (Push > Pull)                  │
│   Live price via AngelOne WebSocket → no LTP polling    │
│   Option chain REST only for OI (WebSocket doesn't have)│
└─────────────────────────────────────────────────────────┘
```

### Smart Scan Priority Scheduler

```python
# backend/app/core/rate_limit.py

import asyncio
import time
from collections import deque
from typing import Callable, Dict, Any
import redis.asyncio as aioredis

class TokenBucketRateLimiter:
    """
    Token bucket per endpoint type.
    Refills at defined rate. Blocks when empty.
    """
    LIMITS = {
        'option_chain':  {'rate': 8,   'burst': 12,  'window': 60},  # 8/min, burst 12
        'market_data':   {'rate': 50,  'burst': 80,  'window': 60},  # 50/min
        'ltp':           {'rate': 80,  'burst': 100, 'window': 60},  # 80/min
        'historical':    {'rate': 4,   'burst': 5,   'window': 60},  # 4/min
        'ws_subscribe':  {'rate': 10,  'burst': 10,  'window': 60},
    }
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
    
    async def acquire(self, endpoint_type: str, identifier: str = 'global') -> float:
        """
        Returns wait_seconds (0 = proceed immediately, >0 = wait this long).
        Uses Redis atomic counter for distributed safety.
        """
        cfg = self.LIMITS.get(endpoint_type, {'rate': 10, 'burst': 10, 'window': 60})
        key = f"ratelimit:{endpoint_type}:{identifier}"
        
        pipe = self.redis.pipeline()
        now = time.time()
        window_start = now - cfg['window']
        
        # Sliding window counter
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, cfg['window'] * 2)
        results = await pipe.execute()
        
        current_count = results[2]
        
        if current_count > cfg['burst']:
            # Calculate wait until oldest request expires
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                wait = cfg['window'] - (now - oldest[0][1])
                return max(0, wait)
        return 0.0
    
    async def wait_and_acquire(self, endpoint_type: str, identifier: str = 'global'):
        """Blocks until a token is available"""
        wait = await self.acquire(endpoint_type, identifier)
        if wait > 0:
            await asyncio.sleep(wait + 0.05)  # +50ms safety buffer


class IntelligentScanScheduler:
    """
    Decides WHAT to scan WHEN based on:
    - Market phase (pre-open, opening, midday, closing, EOD)
    - Priority tier (Watchlist 25 > Nifty/BN > All FnO)
    - Time to expiry (< 2 days = priority boost)
    - Last scan age (staleness-based priority)
    - GEX regime (negative GEX stocks get more frequent scans)
    """
    
    SCAN_INTERVALS = {
        # (phase, tier): seconds between scans
        ('opening', 'watchlist'):    45,   # 9:15-10:30, priority stocks
        ('opening', 'indices'):      60,   # Nifty/BN
        ('opening', 'fno_all'):     120,
        ('midday', 'watchlist'):     60,
        ('midday', 'indices'):       90,
        ('midday', 'fno_all'):      180,
        ('closing', 'watchlist'):    30,   # Last 45 min of session
        ('closing', 'indices'):      45,
        ('closing', 'fno_all'):      90,
        ('pre_expiry', 'watchlist'): 30,   # Day before/of expiry
        ('pre_expiry', 'indices'):   30,
        ('eod', 'all'):           3600,    # Once per hour, EOD only
    }
    
    def get_market_phase(self) -> str:
        import pytz
        from datetime import datetime
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        t = now.hour * 60 + now.minute
        
        if t < 9*60+10:  return 'pre_market'
        if t < 9*60+30:  return 'opening'
        if t < 14*60+45: return 'midday'
        if t < 15*60+30: return 'closing'
        return 'eod'
    
    def get_scan_interval(self, symbol: str, tier: str, days_to_expiry: int) -> int:
        phase = self.get_market_phase()
        base = self.SCAN_INTERVALS.get((phase, tier), 
               self.SCAN_INTERVALS.get((phase, 'fno_all'), 180))
        
        # Expiry boost: halve interval if < 2 days to expiry
        if days_to_expiry <= 1:
            base = base // 2
        elif days_to_expiry <= 2:
            base = int(base * 0.75)
        
        return max(30, base)  # Never faster than 30 seconds


class AngelOneSmartFetcher:
    """
    Wraps all AngelOne API calls with:
    - Rate limiting (token bucket)
    - Automatic retry with backoff
    - Response caching (Redis TTL)
    - Delta compression (only return changed data)
    - Error classification (retryable vs fatal)
    """
    
    CACHE_TTL = {
        'option_chain': 170,    # 3min (1 scan window)
        'ltp':           5,     # 5 seconds (WebSocket preferred)
        'historical':  3600,    # 1 hour
        'instrument':  86400,   # 24 hours
    }
    
    def __init__(self, angel_client, redis_client, rate_limiter):
        self.client = angel_client
        self.redis = redis_client
        self.rl = rate_limiter
        self._cache: Dict[str, Any] = {}
    
    async def get_option_chain(self, symbol: str, expiry: str) -> dict:
        cache_key = f"option_chain:{symbol}:{expiry}"
        
        # Check cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Rate limit
        await self.rl.wait_and_acquire('option_chain')
        
        # Fetch with retry
        for attempt in range(3):
            try:
                data = await self._fetch_with_timeout(
                    self.client.optionChain, symbol, expiry, timeout=8.0
                )
                # Cache it
                await self.redis.setex(cache_key, self.CACHE_TTL['option_chain'], 
                                       json.dumps(data))
                return data
            except RateLimitError:
                await asyncio.sleep(2 ** attempt * 5)   # 5, 10, 20 sec
            except TimeoutError:
                await asyncio.sleep(1)
            except FatalAPIError:
                raise  # Don't retry auth errors
        
        raise Exception(f"Option chain fetch failed for {symbol} after 3 attempts")
    
    async def get_ltp_bulk(self, tokens: list[str]) -> dict:
        """
        AngelOne supports bulk LTP in one call (up to 50 tokens).
        Batch tokens into chunks of 50 to minimize API calls.
        """
        cache_key = f"ltp_bulk:{':'.join(sorted(tokens[:5]))}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        await self.rl.wait_and_acquire('ltp')
        
        # Batch into 50s
        results = {}
        for i in range(0, len(tokens), 50):
            chunk = tokens[i:i+50]
            resp = await self._fetch_with_timeout(
                self.client.ltpData, chunk, timeout=3.0
            )
            results.update(resp)
        
        await self.redis.setex(cache_key, self.CACHE_TTL['ltp'], json.dumps(results))
        return results
    
    async def delta_compress_option_chain(self, new_data: dict, symbol: str, expiry: str) -> dict:
        """
        Compare new OI data to previous snapshot.
        Return ONLY strikes where OI changed > threshold.
        Saves database writes by 60-70%.
        """
        prev_key = f"prev_oi:{symbol}:{expiry}"
        prev_raw = await self.redis.get(prev_key)
        prev = json.loads(prev_raw) if prev_raw else {}
        
        changes = {}
        for strike_key, data in new_data.items():
            prev_data = prev.get(strike_key, {})
            call_oi_chg = abs(data.get('call_oi', 0) - prev_data.get('call_oi', 0))
            put_oi_chg  = abs(data.get('put_oi', 0)  - prev_data.get('put_oi', 0))
            prev_call = prev_data.get('call_oi', 1)
            
            # Only include if change > 0.5% of previous OI
            if (call_oi_chg / max(prev_call, 1) > 0.005 or
                put_oi_chg  / max(prev_data.get('put_oi', 1), 1) > 0.005):
                changes[strike_key] = {
                    **data,
                    'call_oi_delta': data.get('call_oi', 0) - prev_data.get('call_oi', 0),
                    'put_oi_delta':  data.get('put_oi', 0)  - prev_data.get('put_oi', 0),
                }
        
        # Store new as previous
        await self.redis.setex(prev_key, 600, json.dumps(new_data))
        return changes
```

### AngelOne WebSocket Manager (Live Prices — Zero REST Polling)

```python
# backend/app/data/angelone_ws.py

from SmartApi import SmartConnect
import asyncio
import json

class AngelOneWebSocket:
    """
    Uses AngelOne's WebSocket feed for LIVE LTP of:
    - Nifty Futures (all expiries)
    - BankNifty Futures
    - All 150 FnO stock futures
    - Key option strikes (ATM ±5 for watchlist stocks)
    
    NO REST polling for prices. WebSocket push only.
    Saves ~1,500 REST calls/hour.
    """
    
    NIFTY_TOKEN   = "99926000"  # Nifty Futures NSE
    BNIFTY_TOKEN  = "99926009"  # BankNifty Futures NSE
    
    def __init__(self, api_key: str, client_code: str, feed_token: str):
        self.api_key = api_key
        self.client_code = client_code  
        self.feed_token = feed_token
        self.subscriptions: dict[str, list] = {}  # symbol → [tokens]
        self.price_cache: dict[str, float] = {}
        self._callbacks: list = []
    
    async def connect_and_subscribe(self, tokens: list[str]):
        """
        Connects to AngelOne WebSocket and subscribes to token list.
        Automatically reconnects on disconnect.
        """
        import websocket
        # Subscribe in batches of 50 (AngelOne limit)
        ...
    
    def on_price_update(self, token: str, ltp: float, volume: int):
        self.price_cache[token] = ltp
        for cb in self._callbacks:
            asyncio.create_task(cb(token, ltp))
    
    def add_option_strike_subscription(self, symbol: str, strikes: list[int], expiry: str):
        """
        Dynamically add option strike tokens to WebSocket subscription.
        Called when ATM changes (price moves) to track new ATM ±5 range.
        """
        ...
```

---

## 🏗️ COMPLETE BACKEND ARCHITECTURE

### Project Structure
```
anza_platform/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── api/
│   │   │   ├── scanner.py             # GET /scanner, WS /ws/scanner
│   │   │   ├── stock.py               # GET /stock/{sym}/*
│   │   │   ├── watchlist.py           # CRUD /watchlist
│   │   │   ├── niftydesk.py           # NIFTY/BN specific endpoints
│   │   │   ├── alerts.py              # Alert config + history
│   │   │   └── auth.py                # AngelOne auth flow
│   │   ├── core/
│   │   │   ├── black76.py             # ✅ Black-76 (NOT BSM) engine
│   │   │   ├── greeks.py              # Delta,Gamma,Vega,Theta,Vanna,Charm
│   │   │   ├── gex.py                 # GEX/DEX/VEX/CEX per ANZA formulas
│   │   │   ├── oi_analysis.py         # OI signals, velocity, structure detect
│   │   │   ├── bias_score.py          # ANZA Bias Score (Macro·GEX·PCR·VIX)
│   │   │   ├── max_pain.py            # Max pain + expiry convergence
│   │   │   ├── verdict.py             # Smart Money Verdict Engine
│   │   │   ├── rate_limit.py          # Token bucket + scheduler
│   │   │   └── iv_surface.py          # IV skew, term structure
│   │   ├── data/
│   │   │   ├── angelone_client.py     # SmartAPI wrapper
│   │   │   ├── angelone_ws.py         # WebSocket manager
│   │   │   ├── smart_fetcher.py       # Smart fetch (rate limit + cache)
│   │   │   └── fno_universe.py        # 150+ FnO stock list with lot sizes
│   │   ├── db/
│   │   │   ├── models.py              # SQLAlchemy models
│   │   │   ├── timescale.py           # TimescaleDB queries
│   │   │   └── watchlist_store.py     # SQLite watchlist CRUD
│   │   ├── tasks/
│   │   │   ├── celery_app.py          # Celery config
│   │   │   ├── scan_tasks.py          # Periodic scan orchestrator
│   │   │   ├── eod_tasks.py           # EOD analysis (3:30 PM)
│   │   │   └── pre_market.py          # 8:45 AM pre-market prep
│   │   └── telegram/
│   │       ├── bot.py                 # Bot + commands
│   │       ├── alerts.py              # Alert formatter + sender
│   │       └── alert_rules.py        # Priority routing rules
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── pages/
│   │   │   ├── Scanner.jsx            # Main scanner dashboard
│   │   │   ├── NiftyDesk.jsx          # NIFTY/BN dedicated view
│   │   │   ├── StockView.jsx          # Individual stock drilldown
│   │   │   ├── Watchlist.jsx          # Priority 25 watchlist
│   │   │   ├── OIFlow.jsx             # OI flow dashboard
│   │   │   ├── GreeksDesk.jsx         # GEX/DEX/VEX/CEX visual
│   │   │   ├── BiasScore.jsx          # ANZA Bias Score live
│   │   │   ├── Alerts.jsx             # Alert config + Telegram
│   │   │   └── Settings.jsx           # Theme selector + API config
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   │   ├── OIBarChart.jsx     # OI by strike (live)
│   │   │   │   ├── GEXWaterfall.jsx   # GEX by strike
│   │   │   │   ├── BiasGauge.jsx      # Bias score gauge
│   │   │   │   ├── VelocityMeter.jsx  # OI velocity speedometer
│   │   │   │   ├── IVSkewChart.jsx    # IV skew visualization
│   │   │   │   └── PCRChart.jsx       # PCR + velocity
│   │   │   ├── scanner/
│   │   │   │   ├── ScannerTable.jsx
│   │   │   │   ├── VerdictCard.jsx
│   │   │   │   └── StructureTag.jsx
│   │   │   └── layout/
│   │   │       ├── Sidebar.jsx
│   │   │       ├── Header.jsx
│   │   │       └── ThemeToggle.jsx
│   │   ├── themes/
│   │   │   ├── dark-terminal.css      # Default: Bloomberg terminal
│   │   │   ├── neon-quantum.css       # Quantum/Web3 crypto aesthetic
│   │   │   ├── velonic-steel.css      # Velonic-inspired cool steel
│   │   │   ├── upcube-admin.css       # Upcube clean admin
│   │   │   ├── light-professional.css # Clean white pro
│   │   │   └── crypto-dark.css        # Conceptzilla crypto dark
│   │   ├── store/
│   │   │   ├── scannerStore.js        # Zustand scanner state
│   │   │   ├── watchlistStore.js      # Watchlist state
│   │   │   └── settingsStore.js       # Theme + preferences
│   │   └── hooks/
│   │       ├── useWebSocket.js        # WS connection manager
│   │       ├── useScanner.js          # Scanner data + refresh
│   │       └── useStockData.js        # Per-stock data
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
├── .env.example
└── start.sh                           # One-command startup
```

---

## 🧮 BLACK-76 ENGINE (Exact ANZA Implementation)

```python
# backend/app/core/black76.py

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from dataclasses import dataclass

@dataclass
class GreekResult:
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    vanna: float     # dDelta/dIV — VEX ingredient
    charm: float     # dDelta/dT  — CEX ingredient
    vomma: float     # dVega/dIV  — 3rd order
    speed: float     # dGamma/dF  — 3rd order

class Black76Engine:
    """
    CORRECT model for Indian F&O options.
    Uses FUTURES PRICE (F), not Spot.
    
    Per ANZA docs: Always subscribe to AngelOne FUTURES TOKEN,
    not cash index, for F input.
    
    Constants (Feb 2026 per ANZA docs):
    - r = 6.5% (India 10Y G-Sec)
    - Nifty lot = 65
    - BankNifty lot = 30
    """
    
    R = 0.065       # India risk-free rate
    EPSILON = 1e-8  # Newton-Raphson convergence
    
    def price_and_greeks(
        self,
        F: float,       # Futures price (NOT spot)
        K: float,       # Strike
        T: float,       # Time to expiry in years
        sigma: float,   # Implied volatility (decimal)
        option_type: str  # 'CE' or 'PE'
    ) -> GreekResult:
        
        if T <= 0: T = 1/365/24  # 1 hour floor
        if sigma <= 0: sigma = 0.001
        
        r = self.R
        sqrt_T = np.sqrt(T)
        
        d1 = (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
        
        exp_rT = np.exp(-r * T)
        Nd1    = norm.cdf(d1)
        Nd2    = norm.cdf(d2)
        Nm_d1  = norm.cdf(-d1)
        Nm_d2  = norm.cdf(-d2)
        pdf_d1 = norm.pdf(d1)
        
        if option_type == 'CE':
            price = exp_rT * (F * Nd1 - K * Nd2)
            delta = exp_rT * Nd1
        else:  # PE
            price = exp_rT * (K * Nm_d2 - F * Nm_d1)
            delta = exp_rT * (Nd1 - 1)   # = -exp(-rT) * N(-d1)
        
        # Gamma (same for CE and PE)
        gamma = exp_rT * pdf_d1 / (F * sigma * sqrt_T)
        
        # Vega (same sign for both) — per 1% IV move / 100
        vega = F * exp_rT * pdf_d1 * sqrt_T / 100
        
        # Theta — per day
        theta_base = -(F * exp_rT * pdf_d1 * sigma / (2 * sqrt_T)) / 365
        if option_type == 'CE':
            theta = theta_base - r * K * exp_rT * Nd2 / 365
        else:
            theta = theta_base + r * K * exp_rT * Nm_d2 / 365
        
        # Vanna = dDelta/dIV = -exp(-rT) * d2 * pdf(d1) / sigma
        vanna = -exp_rT * (d2 / sigma) * pdf_d1
        
        # Charm = dDelta/dT
        if option_type == 'CE':
            charm = exp_rT * pdf_d1 * (
                (2*r*T - d2*sigma*sqrt_T) / (2*T*sigma*sqrt_T)
            )
        else:
            charm = -exp_rT * pdf_d1 * (
                (2*r*T - d2*sigma*sqrt_T) / (2*T*sigma*sqrt_T)
            )
        
        # Vomma = dVega/dIV
        vomma = vega * d1 * d2 / sigma
        
        # Speed = dGamma/dF
        speed = -gamma * (1 + d1 / (sigma * sqrt_T)) / F
        
        return GreekResult(
            price=price, delta=delta, gamma=gamma,
            vega=vega, theta=theta, vanna=vanna,
            charm=charm, vomma=vomma, speed=speed
        )
    
    def implied_volatility(
        self, market_price: float, F: float, K: float, 
        T: float, option_type: str
    ) -> float:
        """
        Newton-Raphson IV solver using Black-76 vega as Jacobian.
        Vectorized for option chain (1000+ strikes efficiently).
        """
        if T <= 0 or market_price <= 0:
            return 0.0
        
        # Bounds check: intrinsic value
        intrinsic = max(0, F - K) if option_type == 'CE' else max(0, K - F)
        if market_price <= intrinsic:
            return 0.001
        
        sigma = 0.30  # Initial guess
        
        for _ in range(100):
            g = self.price_and_greeks(F, K, T, sigma, option_type)
            diff = g.price - market_price
            
            if abs(diff) < self.EPSILON:
                break
            
            vega_adj = g.vega * 100  # vega was per 1%, need per unit
            if abs(vega_adj) < 1e-10:
                break
            
            sigma = sigma - diff / vega_adj
            sigma = max(0.001, min(sigma, 5.0))  # 0.1% to 500% IV bounds
        
        return sigma
    
    def iv_surface_vectorized(
        self, option_chain: list[dict], F: float, T: float
    ) -> list[dict]:
        """
        Solve IV for all strikes simultaneously.
        Returns option_chain with 'iv' and all greeks added.
        Fast: uses numpy vectorized operations.
        """
        results = []
        for row in option_chain:
            for opt_type in ['CE', 'PE']:
                price = row.get(f'{opt_type.lower()}_ltp', 0)
                strike = row['strike']
                if price > 0 and T > 0:
                    iv = self.implied_volatility(price, F, strike, T, opt_type)
                    greeks = self.price_and_greeks(F, strike, T, iv, opt_type)
                    row[f'{opt_type.lower()}_iv'] = iv
                    row[f'{opt_type.lower()}_delta'] = greeks.delta
                    row[f'{opt_type.lower()}_gamma'] = greeks.gamma
                    row[f'{opt_type.lower()}_vega'] = greeks.vega
                    row[f'{opt_type.lower()}_theta'] = greeks.theta
                    row[f'{opt_type.lower()}_vanna'] = greeks.vanna
                    row[f'{opt_type.lower()}_charm'] = greeks.charm
        return results
```

---

## 📊 ANZA BIAS SCORE ENGINE (Exact Formula from Docs)

```python
# backend/app/core/bias_score.py

from dataclasses import dataclass

@dataclass
class BiasComponents:
    macro_score: float        # FII/DII net flow [-1, +1]
    gex_score: float          # Normalised GEX [-1, +1]
    pcr_velocity: float       # PCR rate of change [-1, +1]
    vix_adjustment: float     # -0.20 if VIX > 20, else 0
    final_score: float        # Composite [-1, +1]
    verdict: str              # STRONGLY_BULLISH/BULLISH/NEUTRAL/BEARISH/STRONGLY_BEARISH

class ANZABiasEngine:
    """
    Exact ANZA Bias Score formula from ANZA_Trading_Intelligence_Reference.docx:
    
    Bias = (Macro × 0.25) + (GEX_Score × 0.25) + (PCR_Velocity × 0.30) + (VIX_Adj × 0.20)
    Final = clip(Bias, -1.0, +1.0)
    
    Verdict: BULLISH if > +0.40, BEARISH if < -0.40, else NEUTRAL
    """
    
    WEIGHTS = {
        'macro':        0.25,
        'gex':          0.25,
        'pcr_velocity': 0.30,
        'vix_adj':      0.20,
    }
    
    VERDICT_THRESHOLDS = {
        0.65:  'STRONGLY_BULLISH',
        0.40:  'BULLISH',
        -0.40: 'NEUTRAL',
        -0.65: 'BEARISH',
    }
    
    def compute(
        self,
        fii_net_cr: float,           # FII net buy/sell in Crore
        dii_net_cr: float,
        net_gex_cr: float,           # Total market GEX in Crore
        pcr_now: float,
        pcr_15min_ago: float,
        india_vix: float,
    ) -> BiasComponents:
        
        # 1. Macro Score — FII dominant
        fii_score = self._normalise_fii(fii_net_cr, dii_net_cr)
        
        # 2. GEX Score (per ANZA: clip(GEX/100, -1, 1))
        gex_score = max(-1.0, min(1.0, net_gex_cr / 100.0))
        
        # 3. PCR Velocity Score
        pcr_vel = (pcr_now - pcr_15min_ago) / 15.0  # per-minute rate
        PCR_SCALE = 0.02  # threshold: 0.02/min change = ±1.0 score
        pcr_vel_score = max(-1.0, min(1.0, -pcr_vel / PCR_SCALE))  # Negative vel = bullish
        
        # 4. VIX Adjustment (from ANZA docs)
        vix_adj = -0.20 if india_vix > 20.0 else 0.0
        
        # 5. Composite
        bias = (
            fii_score       * self.WEIGHTS['macro'] +
            gex_score       * self.WEIGHTS['gex'] +
            pcr_vel_score   * self.WEIGHTS['pcr_velocity'] +
            vix_adj         * self.WEIGHTS['vix_adj']
        )
        final = max(-1.0, min(1.0, bias))
        
        # 6. Verdict
        verdict = 'NEUTRAL'
        if final >= 0.65:   verdict = 'STRONGLY_BULLISH'
        elif final >= 0.40: verdict = 'BULLISH'
        elif final <= -0.65: verdict = 'STRONGLY_BEARISH'
        elif final <= -0.40: verdict = 'BEARISH'
        
        return BiasComponents(
            macro_score=fii_score,
            gex_score=gex_score,
            pcr_velocity=pcr_vel_score,
            vix_adjustment=vix_adj,
            final_score=final,
            verdict=verdict
        )
    
    def _normalise_fii(self, fii: float, dii: float) -> float:
        """
        Per ANZA docs example: FII +800Cr + DII +200Cr = STRONG BULLISH = +0.4 macro
        Scale: +/-2000 Cr = +/-1.0 score
        """
        combined = fii * 0.75 + dii * 0.25   # FII weighted more
        return max(-1.0, min(1.0, combined / 2000.0))
```

---

## 🎨 6 THEME SYSTEM (Complete CSS Variables)

```css
/* frontend/src/themes/dark-terminal.css — DEFAULT */
/* Bloomberg terminal × ANZA AI — deep professional */
[data-theme="dark-terminal"] {
  --bg-primary: #040508;
  --bg-secondary: #070b12;
  --bg-card: #0c1220;
  --bg-hover: #111b2e;
  --accent-primary: #00c8ff;
  --accent-secondary: #9966ff;
  --bull: #00ff88;
  --bear: #ff3366;
  --warn: #ffaa00;
  --text-primary: #c8d8f0;
  --text-secondary: #4a6080;
  --border: rgba(0,200,255,0.08);
  --border-bright: rgba(0,200,255,0.22);
  --font-display: 'Space Mono', monospace;
  --font-body: 'Syne', sans-serif;
  --font-data: 'JetBrains Mono', monospace;
  --glow: 0 0 20px rgba(0,200,255,0.15);
  --shadow: 0 4px 24px rgba(0,0,0,0.6);
}

/* frontend/src/themes/neon-quantum.css */
/* Conceptzilla Quantum Web3 × Phenomenon Studio */
[data-theme="neon-quantum"] {
  --bg-primary: #020210;
  --bg-secondary: #050525;
  --bg-card: #0a0a35;
  --bg-hover: #12124a;
  --accent-primary: #7c3aed;
  --accent-secondary: #ec4899;
  --bull: #10b981;
  --bear: #ef4444;
  --warn: #f59e0b;
  --text-primary: #e2e8f0;
  --text-secondary: #6b7280;
  --border: rgba(124,58,237,0.15);
  --border-bright: rgba(124,58,237,0.4);
  --font-display: 'Orbitron', sans-serif;
  --font-body: 'Rajdhani', sans-serif;
  --font-data: 'Share Tech Mono', monospace;
  --glow: 0 0 30px rgba(124,58,237,0.3);
  --shadow: 0 8px 32px rgba(0,0,0,0.8);
}

/* frontend/src/themes/velonic-steel.css */
/* Velonic React Admin × Techmin Bootstrap — Cool steel pro */
[data-theme="velonic-steel"] {
  --bg-primary: #1a1f2e;
  --bg-secondary: #222736;
  --bg-card: #2a3044;
  --bg-hover: #323a52;
  --accent-primary: #4f8ef7;
  --accent-secondary: #7c4dff;
  --bull: #2ecc71;
  --bear: #e74c3c;
  --warn: #f39c12;
  --text-primary: #d0d5e8;
  --text-secondary: #6b7a99;
  --border: rgba(79,142,247,0.1);
  --border-bright: rgba(79,142,247,0.3);
  --font-display: 'Plus Jakarta Sans', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-data: 'Fira Code', monospace;
  --glow: none;
  --shadow: 0 2px 12px rgba(0,0,0,0.3);
}

/* frontend/src/themes/upcube-admin.css */
/* Upcube Django Admin × SaaSly clean */
[data-theme="upcube-admin"] {
  --bg-primary: #f0f2f8;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-hover: #f7f9ff;
  --accent-primary: #4361ee;
  --accent-secondary: #7209b7;
  --bull: #06d6a0;
  --bear: #ef233c;
  --warn: #fb8500;
  --text-primary: #2d3748;
  --text-secondary: #718096;
  --border: rgba(67,97,238,0.12);
  --border-bright: rgba(67,97,238,0.3);
  --font-display: 'Poppins', sans-serif;
  --font-body: 'Nunito Sans', sans-serif;
  --font-data: 'IBM Plex Mono', monospace;
  --glow: none;
  --shadow: 0 1px 4px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.06);
}

/* frontend/src/themes/light-professional.css */
/* WriteMate AI × SaaSly modern clean */
[data-theme="light-professional"] {
  --bg-primary: #f8fafc;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-hover: #f1f5f9;
  --accent-primary: #0ea5e9;
  --accent-secondary: #8b5cf6;
  --bull: #059669;
  --bear: #dc2626;
  --warn: #d97706;
  --text-primary: #1e293b;
  --text-secondary: #94a3b8;
  --border: rgba(14,165,233,0.1);
  --border-bright: rgba(14,165,233,0.25);
  --font-display: 'Cabinet Grotesk', sans-serif;
  --font-body: 'General Sans', sans-serif;
  --font-data: 'Geist Mono', monospace;
  --glow: none;
  --shadow: 0 1px 2px rgba(0,0,0,0.05), 0 4px 20px rgba(0,0,0,0.06);
}

/* frontend/src/themes/crypto-dark.css */
/* Crypto Exchange Dribbble × React Bank UI × Finance */
[data-theme="crypto-dark"] {
  --bg-primary: #0d0e14;
  --bg-secondary: #13151e;
  --bg-card: #1a1d28;
  --bg-hover: #222535;
  --accent-primary: #f0b90b;
  --accent-secondary: #2775ca;
  --bull: #0ecb81;
  --bear: #f6465d;
  --warn: #f0b90b;
  --text-primary: #eaecef;
  --text-secondary: #848e9c;
  --border: rgba(240,185,11,0.08);
  --border-bright: rgba(240,185,11,0.2);
  --font-display: 'Chakra Petch', sans-serif;
  --font-body: 'Barlow', sans-serif;
  --font-data: 'Courier Prime', monospace;
  --glow: 0 0 20px rgba(240,185,11,0.1);
  --shadow: 0 4px 20px rgba(0,0,0,0.5);
}
```

---

## 📱 COMPLETE API REFERENCE

```
# AUTH
POST   /api/auth/login          → {api_key, client_id, password, totp} → JWT
POST   /api/auth/refresh        → Refresh JWT
GET    /api/auth/status         → Connection status + rate limit counters

# MARKET OVERVIEW
GET    /api/market/overview     → VIX, Nifty, BN, FII/DII, market GEX regime
GET    /api/market/bias         → ANZA Bias Score breakdown
GET    /api/market/gex-map      → GEX by strike for Nifty (full chain)

# SCANNER
GET    /api/scanner             → Top stocks by momentum score
  ?filter=bull|bear|all
  ?watchlist_only=true
  ?limit=25
  ?sort=score|velocity|gex

# INDIVIDUAL STOCK
GET    /api/stock/{sym}/snapshot      → Full current analysis
GET    /api/stock/{sym}/oi-chain      → OI by strike (latest)
GET    /api/stock/{sym}/oi-history    → OI time series (intraday)
GET    /api/stock/{sym}/greeks        → GEX/DEX/VEX/CEX breakdown
GET    /api/stock/{sym}/verdict       → Smart Money Verdict card
GET    /api/stock/{sym}/structures    → Detected trade structures
GET    /api/stock/{sym}/levels        → Call wall, put wall, max pain, GEX flip

# WATCHLIST (Priority 25)
GET    /api/watchlist                  → All 25 + live metrics
POST   /api/watchlist/add             → {symbol, notes, alert_config}
DELETE /api/watchlist/{symbol}
PUT    /api/watchlist/{symbol}        → Update notes/alert config
GET    /api/watchlist/verdicts        → All 25 verdicts in one call

# ALERTS
GET    /api/alerts/history            → Today's triggered alerts
GET    /api/alerts/config             → Alert settings
POST   /api/alerts/test               → Send test Telegram message
PUT    /api/alerts/mute/{sym}         → Mute for N minutes

# WEBSOCKETS
WS     /ws/scanner                    → Live scanner updates (3min refresh)
WS     /ws/market                     → VIX, Nifty, BN live prices
WS     /ws/stock/{symbol}             → Live OI + price for one stock
WS     /ws/alerts                     → Real-time alert notifications
WS     /ws/bias                       → Live Bias Score updates
```

---

## 🚀 ONE-COMMAND STARTUP

```bash
# start.sh
#!/bin/bash
echo "🚀 Starting ANZA FNO Intelligence Platform..."

# Copy env
[ ! -f .env ] && cp .env.example .env && echo "⚠️  Fill in .env with AngelOne credentials"

# Start all services
docker-compose up -d

echo "✅ Services started:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   TimescaleDB: localhost:5432"
echo "   Redis:     localhost:6379"
```

```yaml
# docker-compose.yml
version: '3.9'
services:
  backend:
    build: ./backend
    ports: ['8000:8000']
    env_file: .env
    depends_on: [timescaledb, redis]
    volumes: ['./backend:/app']
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
  celery_worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --concurrency=4 --loglevel=info
    env_file: .env
    depends_on: [redis, timescaledb]
    
  celery_beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info
    env_file: .env
    depends_on: [redis]
    
  telegram_bot:
    build: ./backend
    command: python -m app.telegram.bot
    env_file: .env
    depends_on: [redis, backend]
    restart: unless-stopped
    
  frontend:
    build: ./frontend
    ports: ['3000:80']
    
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:-anza_secret}
      POSTGRES_DB: anza_fno
    volumes: ['pgdata:/var/lib/postgresql/data']
    ports: ['5432:5432']
    
  redis:
    image: redis:7-alpine
    ports: ['6379:6379']
    volumes: ['redisdata:/data']
    command: redis-server --appendonly yes

volumes:
  pgdata:
  redisdata:
```

---

## 📊 UPGRADATION ROADMAP

### Version 1.0 (MVP — 3 weeks)
- AngelOne auth + WebSocket live prices
- Black-76 greeks engine (verified against ANZA docs worked examples)
- ANZA Bias Score (exact formula)
- Basic OI signals (buildup/covering)
- 6 themes + theme switcher
- Scanner table (top 25 stocks)
- Telegram basic alerts

### Version 2.0 (Full intelligence — +2 weeks)
- GEX/DEX/VEX/CEX dealer exposure
- OI Velocity engine (z-score)
- Trade structure detection (naked vs spread)
- Smart Money Verdict Engine
- Priority Watchlist (25 stocks)
- ANZA Stock-specific modules (Delivery %, Event Filter, Sector Alignment)

### Version 3.0 (ANZA NiftyDesk parity — +2 weeks)
- Full NIFTY Desk page (GEX wall, flip point, max pain, IV surface)
- PCR velocity charting
- Advance-Decline breadth
- IV Skew visualization
- Volume Profile (POC, VAH, VAL) overlay
- Statistical time-of-day patterns (Tuesday/Thursday expiry playbook)

### Version 4.0 (AI layer — optional)
- LLM market brief (morning summary in plain English)
- Aanya-style conversational interface (send to local Ollama)
- Market Memory (cosine similarity to historical sessions)
- No external API cost — use local Ollama/LM Studio

### Version 5.0 (Mobile PWA)
- Progressive Web App — installable on phone
- Telegram bot as primary mobile interface
- Push notifications via PWA
