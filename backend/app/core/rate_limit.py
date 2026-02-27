# backend/app/core/rate_limit.py

import asyncio
import time
from collections import deque
from typing import Callable, Dict, Any
import redis.asyncio as aioredis
from datetime import datetime
import pytz

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
