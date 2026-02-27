# 🔥 INDIA FNO SMART FLOW MONITOR — DEEP DIVE V2
## Maximum Technical Edge: OI Velocity, Spread vs Naked Detection, Smart Money Verdict Engine, Telegram Alerts, Priority Watchlist

---

## 🧠 CORE INTELLIGENCE UPGRADES IN V2

> The platform now answers **4 questions** per stock, every 3 minutes:
> 1. **WHO** is entering? (Smart money fingerprint vs retail noise)
> 2. **WHAT** are they doing? (Naked directional, 2-leg spread, hedge, or writer?)
> 3. **HOW FAST** are they doing it? (OI velocity — urgency & conviction)
> 4. **WHAT DOES IT MEAN?** (Composite Verdict: BUY SETUP / SHORT SETUP / WAIT / TRAP)

---

## 🆕 MODULE 6: OI VELOCITY ENGINE (NEW — DEEP EDGE)

### Why OI Velocity Matters
> Standard OI tells you WHAT. Velocity tells you **HOW URGENTLY**. An institution that adds 50,000 contracts in 3 minutes has 10x more conviction than one adding 50,000 over 3 hours.

### Multi-Tier Velocity Calculation

```python
import numpy as np
from dataclasses import dataclass
from typing import Optional
from collections import deque

@dataclass
class OISnapshot:
    timestamp: float
    strike: int
    option_type: str   # CE / PE
    oi: int
    volume: int
    ltp: float
    iv: float

class OIVelocityEngine:
    """
    Tracks OI change RATE, ACCELERATION, and JERK across multiple timeframes.
    Inspired by physics: position=OI, velocity=dOI/dt, acceleration=d²OI/dt²
    """
    
    def __init__(self, symbol: str, strike: int, option_type: str):
        self.symbol = symbol
        self.strike = strike
        self.option_type = option_type
        # Rolling window of (timestamp, oi) tuples — 60 snapshots = 3hr at 3min intervals
        self.history: deque = deque(maxlen=60)
    
    def add_snapshot(self, snapshot: OISnapshot):
        self.history.append((snapshot.timestamp, snapshot.oi, snapshot.volume))
    
    def velocity(self, window_minutes: int = 15) -> float:
        """OI change per minute over last N minutes"""
        cutoff = len(self.history)
        window_bars = window_minutes // 3   # 3min resolution
        if len(self.history) < 2:
            return 0.0
        recent = list(self.history)[-min(window_bars, len(self.history)):]
        if len(recent) < 2:
            return 0.0
        delta_oi = recent[-1][1] - recent[0][1]
        delta_t = (recent[-1][0] - recent[0][0]) / 60   # seconds to minutes
        return delta_oi / max(delta_t, 1)
    
    def acceleration(self) -> float:
        """Is velocity speeding up or slowing down?"""
        v_recent = self.velocity(window_minutes=15)
        v_earlier = self._velocity_at_offset(offset_bars=10, window_bars=5)
        return v_recent - v_earlier
    
    def velocity_zscore(self) -> float:
        """
        How abnormal is current velocity vs historical baseline?
        Z-score > 2.0 = statistically unusual (smart money activity)
        Z-score > 3.0 = extreme (institutional accumulation)
        """
        all_velocities = self._compute_rolling_velocities(window=5)
        if len(all_velocities) < 10:
            return 0.0
        mean = np.mean(all_velocities)
        std = np.std(all_velocities)
        if std == 0:
            return 0.0
        return (self.velocity(15) - mean) / std
    
    def volume_oi_divergence(self) -> str:
        """
        Key insight: Volume>OI at a strike = FRESH MONEY (new positions)
        Volume<<OI = mostly closing existing positions
        """
        recent = list(self.history)[-1]
        current_oi = recent[1]
        current_vol = recent[2]
        ratio = current_vol / max(current_oi, 1)
        if ratio > 1.2:    return "EXTREME_FRESH"   # Very rare — nearly all fresh
        elif ratio > 0.6:  return "MOSTLY_FRESH"    # Unusual — smart money entering
        elif ratio > 0.3:  return "MIXED"           # Normal activity
        else:              return "MOSTLY_CLOSING"  # Low conviction
    
    def oi_momentum_score(self) -> int:
        """Combined 0-100 score for this specific strike's OI momentum"""
        score = 0
        v = self.velocity(15)
        z = self.velocity_zscore()
        a = self.acceleration()
        
        # Velocity magnitude (30 pts)
        if abs(v) > 5000: score += 30
        elif abs(v) > 2000: score += 20
        elif abs(v) > 500: score += 10
        
        # Z-score abnormality (40 pts)
        if z > 3.0: score += 40
        elif z > 2.0: score += 28
        elif z > 1.5: score += 15
        
        # Acceleration (positive = building momentum) (20 pts)
        if a > 0 and v > 0: score += 20
        elif a > 0: score += 10
        
        # Vol/OI freshness (10 pts)
        freshness = self.volume_oi_divergence()
        if freshness == "EXTREME_FRESH": score += 10
        elif freshness == "MOSTLY_FRESH": score += 7
        
        return min(100, score)
    
    def _compute_rolling_velocities(self, window: int = 5) -> list:
        hist = list(self.history)
        velocities = []
        for i in range(window, len(hist)):
            delta_oi = hist[i][1] - hist[i-window][1]
            delta_t = (hist[i][0] - hist[i-window][0]) / 60
            velocities.append(delta_oi / max(delta_t, 1))
        return velocities
    
    def _velocity_at_offset(self, offset_bars: int, window_bars: int) -> float:
        hist = list(self.history)
        end = len(hist) - offset_bars
        start = max(0, end - window_bars)
        if end <= 0 or start >= end:
            return 0.0
        delta_oi = hist[end][1] - hist[start][1]
        delta_t = (hist[end][0] - hist[start][0]) / 60
        return delta_oi / max(delta_t, 1)
```

### OI Velocity Alert Thresholds
```python
VELOCITY_ALERTS = {
    # (z_score_threshold, signal, urgency, description)
    'EXTREME': (3.0, '🔴 EXTREME OI SURGE', 'P1', 'Institutional accumulation — act NOW'),
    'STRONG':  (2.0, '🟠 STRONG OI FLOW',  'P2', 'Unusual flow — monitor closely'),
    'MILD':    (1.5, '🟡 ELEVATED OI',      'P3', 'Above average — note direction'),
}
```

---

## 🆕 MODULE 7: TRADE STRUCTURE IDENTIFIER (NEW — NAKED vs SPREAD)

> This is the most complex and valuable module. NSE doesn't give you trade-level data with multi-leg flags, but you CAN infer the structure from **cross-strike OI patterns**.

### Philosophy
```
Naked Call Buy:      Single strike call OI spikes alone
Naked Put Buy:       Single strike put OI spikes alone  
Bull Call Spread:    Lower strike call OI ↑ + Higher strike call OI ↑ simultaneously
Bear Put Spread:     Higher strike put OI ↑ + Lower strike put OI ↑ simultaneously
Synthetic Long:      Call OI ↑ + Put OI ↑ (same or nearby strike) — straddle or strangle
Call Writer (Bear):  Call OI ↑ with price FALLING (writer, not buyer)
Put Writer (Bull):   Put OI ↑ with price RISING (writer = bullish)
Hedge:               OTM Put spike while stock at resistance or post-rally
```

### Cross-Strike Pattern Detection Engine

```python
from enum import Enum
from scipy.stats import pearsonr

class TradeStructure(Enum):
    NAKED_CALL_BUY        = "NAKED_CALL_BUY"
    NAKED_PUT_BUY         = "NAKED_PUT_BUY"
    BULL_CALL_SPREAD      = "BULL_CALL_SPREAD"
    BEAR_PUT_SPREAD       = "BEAR_PUT_SPREAD"
    CALL_RATIO_SPREAD     = "CALL_RATIO_SPREAD"
    STRANGLE_BUY          = "STRANGLE_BUY"
    STRADDLE              = "STRADDLE"
    BULLISH_PUT_WRITE     = "BULLISH_PUT_WRITE"
    BEARISH_CALL_WRITE    = "BEARISH_CALL_WRITE"
    PROTECTIVE_PUT_HEDGE  = "PROTECTIVE_PUT_HEDGE"
    COVERED_CALL          = "COVERED_CALL"
    UNKNOWN               = "UNKNOWN"

@dataclass
class StructureDetection:
    structure: TradeStructure
    confidence: float           # 0.0 - 1.0
    buy_leg: Optional[dict]     # strike, type, oi_change
    sell_leg: Optional[dict]
    net_premium_direction: str  # 'DEBIT' (buyer) or 'CREDIT' (writer)
    directional_bias: str       # BULLISH / BEARISH / NEUTRAL
    conviction: str             # HIGH/MEDIUM/LOW
    explanation: str

class TradeStructureIdentifier:
    """
    Detects multi-leg vs naked structures from OI change patterns.
    Key insight: When TWO strikes' OI change in SAME DIRECTION simultaneously,
    it's almost certainly a spread, not two independent naked buys.
    """
    
    def identify(
        self, 
        symbol: str,
        oi_changes: dict,        # {(strike, 'CE'/'PE'): oi_change_this_snapshot}
        price_change: float,     # % price change same period  
        atm_strike: float,
        lot_size: int,
        velocity_scores: dict    # {(strike, type): velocity_score}
    ) -> list[StructureDetection]:
        
        detections = []
        
        # Step 1: Find all strikes with statistically significant OI change
        significant = self._filter_significant(oi_changes, threshold_pct=30)
        
        if not significant:
            return []
        
        # Step 2: Find correlated pairs (spread legs)
        spread_pairs = self._find_correlated_pairs(significant, oi_changes)
        
        # Step 3: Classify each pair or solo
        for pair in spread_pairs:
            det = self._classify_spread(pair, oi_changes, atm_strike, price_change)
            if det:
                detections.append(det)
        
        # Step 4: Remaining solo OI changes = naked positions
        paired_strikes = {s for pair in spread_pairs for s in pair}
        for strike_type, change in significant.items():
            if strike_type not in paired_strikes:
                det = self._classify_naked(strike_type, change, oi_changes, 
                                          atm_strike, price_change, lot_size)
                if det:
                    detections.append(det)
        
        return detections
    
    def _filter_significant(self, oi_changes: dict, threshold_pct: float = 30) -> dict:
        """Keep only strikes with OI change > threshold% of their current OI"""
        return {k: v for k, v in oi_changes.items() 
                if abs(v) > 500  # minimum 500 contracts
                and oi_changes.get(k, 0) != 0}
    
    def _find_correlated_pairs(self, significant: dict, oi_changes: dict) -> list:
        """
        If two call strikes BOTH gain OI in same 3min window = spread signal.
        Rule: Both same direction change within 2 ATM distances = spread pair.
        """
        pairs = []
        strikes = list(significant.keys())
        
        for i, (s1, t1) in enumerate(strikes):
            for j, (s2, t2) in enumerate(strikes[i+1:], i+1):
                change1 = oi_changes.get((s1,t1), 0)
                change2 = oi_changes.get((s2,t2), 0)
                
                # Same option type (both CE or both PE) = likely spread
                same_type = t1 == t2
                # Both positive OI change = both legs being bought
                same_direction = (change1 > 0 and change2 > 0) or (change1 < 0 and change2 < 0)
                # Magnitude similarity (within 40% of each other = institutional round-lot)
                magnitude_ratio = min(abs(change1), abs(change2)) / max(abs(change1), abs(change2)+1)
                
                if same_type and same_direction and magnitude_ratio > 0.4:
                    pairs.append(((s1,t1), (s2,t2)))
        
        return pairs
    
    def _classify_spread(self, pair: tuple, oi_changes: dict, atm: float, price_chg: float) -> Optional[StructureDetection]:
        (s1, t1), (s2, t2) = pair
        change1 = oi_changes[(s1,t1)]
        change2 = oi_changes[(s2,t2)]
        
        lower_strike = min(s1, s2)
        upper_strike = max(s1, s2)
        both_calls = t1 == 'CE' and t2 == 'CE'
        both_puts = t1 == 'PE' and t2 == 'PE'
        
        # Ratio spread detection: one leg >> other leg
        ratio = max(abs(change1),abs(change2)) / max(min(abs(change1),abs(change2)),1)
        is_ratio_spread = ratio > 2.5
        
        if both_calls:
            if is_ratio_spread:
                return StructureDetection(
                    structure=TradeStructure.CALL_RATIO_SPREAD,
                    confidence=0.72, buy_leg={'strike':lower_strike,'type':'CE'},
                    sell_leg={'strike':upper_strike,'type':'CE'},
                    net_premium_direction='CREDIT' if change2 > change1 else 'DEBIT',
                    directional_bias='BULLISH', conviction='MEDIUM',
                    explanation=f"Call ratio spread {lower_strike}/{upper_strike} — mildly bullish, capped upside"
                )
            return StructureDetection(
                structure=TradeStructure.BULL_CALL_SPREAD,
                confidence=0.80, buy_leg={'strike':lower_strike,'type':'CE'},
                sell_leg={'strike':upper_strike,'type':'CE'},
                net_premium_direction='DEBIT',
                directional_bias='BULLISH', conviction='HIGH',
                explanation=f"Bull Call Spread {lower_strike}/{upper_strike} — DEBIT spread, limited risk, BULLISH bias"
            )
        
        elif both_puts:
            return StructureDetection(
                structure=TradeStructure.BEAR_PUT_SPREAD,
                confidence=0.80, buy_leg={'strike':upper_strike,'type':'PE'},
                sell_leg={'strike':lower_strike,'type':'PE'},
                net_premium_direction='DEBIT',
                directional_bias='BEARISH', conviction='HIGH',
                explanation=f"Bear Put Spread {upper_strike}/{lower_strike} — DEBIT spread, BEARISH bias"
            )
        
        # Mixed: one call + one put = strangle or straddle
        elif t1 != t2:
            distance_atm = abs(s1 - atm) + abs(s2 - atm)
            if distance_atm < atm * 0.03:   # Both near ATM
                return StructureDetection(
                    structure=TradeStructure.STRADDLE,
                    confidence=0.75, buy_leg={'strike':s1,'type':'BOTH'},
                    sell_leg=None,
                    net_premium_direction='DEBIT',
                    directional_bias='NEUTRAL', conviction='HIGH',
                    explanation=f"Straddle near {atm} — betting on BIG MOVE either direction (event play?)"
                )
            else:
                return StructureDetection(
                    structure=TradeStructure.STRANGLE_BUY,
                    confidence=0.70, buy_leg={'strike':min(s1,s2),'type':'PE/CE'},
                    sell_leg=None,
                    net_premium_direction='DEBIT',
                    directional_bias='NEUTRAL', conviction='MEDIUM',
                    explanation=f"Strangle {min(s1,s2)}/{max(s1,s2)} — event play, needs big move to profit"
                )
        
        return None
    
    def _classify_naked(self, strike_type: tuple, change: int, oi_changes: dict, 
                        atm: float, price_chg: float, lot_size: int) -> Optional[StructureDetection]:
        strike, opt_type = strike_type
        moneyness = (strike - atm) / atm * 100   # % away from ATM
        is_otm_call = opt_type == 'CE' and moneyness > 0
        is_otm_put = opt_type == 'PE' and moneyness < 0
        is_itm_call = opt_type == 'CE' and moneyness < -5
        
        # Call OI ↑ but price ↓ = CALL WRITER (bearish)
        is_writer_call = opt_type == 'CE' and change > 0 and price_chg < -0.3
        is_writer_put = opt_type == 'PE' and change > 0 and price_chg > 0.3
        
        # OTM put spike with stock at recent high = PROTECTIVE HEDGE
        is_hedge = (is_otm_put and abs(moneyness) > 5 and price_chg > 1.0)
        
        if is_hedge:
            return StructureDetection(
                structure=TradeStructure.PROTECTIVE_PUT_HEDGE,
                confidence=0.65, buy_leg={'strike':strike,'type':'PE'},
                sell_leg=None,
                net_premium_direction='DEBIT',
                directional_bias='NEUTRAL',
                conviction='LOW',
                explanation=f"Hedge buying {strike} PE — institutional protecting longs, NOT bearish signal"
            )
        
        if is_writer_call:
            return StructureDetection(
                structure=TradeStructure.BEARISH_CALL_WRITE,
                confidence=0.75, buy_leg=None,
                sell_leg={'strike':strike,'type':'CE'},
                net_premium_direction='CREDIT',
                directional_bias='BEARISH', conviction='HIGH',
                explanation=f"Call writer at {strike} — selling resistance, bearish conviction"
            )
        
        if is_writer_put:
            return StructureDetection(
                structure=TradeStructure.BULLISH_PUT_WRITE,
                confidence=0.78, buy_leg=None,
                sell_leg={'strike':strike,'type':'PE'},
                net_premium_direction='CREDIT',
                directional_bias='BULLISH', conviction='HIGH',
                explanation=f"Put writer at {strike} — STRONG bullish signal, collecting premium at support"
            )
        
        premium_moved = abs(change) * lot_size   # total contracts moved
        
        if opt_type == 'CE' and change > 0:
            otm_note = f"({abs(moneyness):.1f}% OTM)" if is_otm_call else "(near ATM)"
            return StructureDetection(
                structure=TradeStructure.NAKED_CALL_BUY,
                confidence=0.85 if moneyness < 5 else 0.70,
                buy_leg={'strike':strike,'type':'CE','moneyness':moneyness},
                sell_leg=None,
                net_premium_direction='DEBIT',
                directional_bias='BULLISH',
                conviction='HIGH' if abs(moneyness) < 3 else 'MEDIUM',
                explanation=f"Naked Call Buy {strike} CE {otm_note} — PURE directional bullish bet. {abs(change):,} contracts."
            )
        
        if opt_type == 'PE' and change > 0:
            return StructureDetection(
                structure=TradeStructure.NAKED_PUT_BUY,
                confidence=0.85 if abs(moneyness) < 5 else 0.70,
                buy_leg={'strike':strike,'type':'PE'},
                sell_leg=None,
                net_premium_direction='DEBIT',
                directional_bias='BEARISH',
                conviction='HIGH',
                explanation=f"Naked Put Buy {strike} PE — PURE bearish directional. {abs(change):,} contracts."
            )
        
        return None
```

### Why This Matters for Your Trading
```
Naked Call Buy      → Match it: buy same strike call (highest leverage)
Bull Call Spread    → Match proportionally: buy same spread (cheaper, less risky)
Call Writer         → Counter: buy put or put spread (they see resistance)
Put Writer          → Match: buy stock/call (strong institutions at support)
Straddle            → Wait for direction, then buy whichever way breaks
Protective Hedge    → IGNORE: not bearish signal, just risk management
```

---

## 🆕 MODULE 8: SMART MONEY VERDICT ENGINE (NEW)

### The 4-Tier Conviction Framework

```python
from enum import Enum

class Verdict(Enum):
    STRONG_BUY   = "⚡ STRONG BUY SETUP"
    BUY_WATCH    = "🟢 BUY WATCHLIST"
    NEUTRAL      = "🟡 WAIT / OBSERVE"
    SELL_WATCH   = "🔴 SHORT WATCHLIST"
    STRONG_SELL  = "🔥 STRONG SHORT SETUP"
    TRAP_WARNING = "⚠️ POSSIBLE TRAP — SKIP"

@dataclass
class SmartMoneyVerdict:
    verdict: Verdict
    confidence_pct: int          # 0-100
    holding_period: str          # "INTRADAY" / "1-2 DAYS" / "3-5 DAYS"
    target_move_pct: float       # Expected % move
    risk_level: str              # LOW / MEDIUM / HIGH
    entry_type: str              # "SPOT" / "CE BUY" / "PE BUY" / "CALL SPREAD" / "PUT SPREAD"
    entry_strike: Optional[int]
    stop_loss_level: float
    key_reasons: list[str]       # Max 4 bullet points
    red_flags: list[str]         # Reasons to be cautious

class SmartMoneyVerdictEngine:
    """
    Synthesizes ALL signals into a final actionable verdict.
    Designed for momentum trades: 1 hour to 5 days max holding.
    """
    
    def generate_verdict(self, symbol: str, ctx: dict) -> SmartMoneyVerdict:
        """
        ctx contains:
          - oi_signal, gex, dex, vex, cex
          - velocity_score, velocity_zscore
          - structure_detections (list of StructureDetection)
          - fii_net_change, pcr, iv_rank
          - price_vs_max_pain, days_to_expiry
          - technicals: rsi, vwap_position, volume_ratio
          - momentum_score (from Module 4)
        """
        score = ctx['momentum_score']
        structures = ctx.get('structure_detections', [])
        vel_z = ctx.get('velocity_zscore', 0)
        
        # TRAP DETECTION first (safety filter)
        trap_score = self._compute_trap_score(ctx, structures)
        if trap_score > 70:
            return SmartMoneyVerdict(
                verdict=Verdict.TRAP_WARNING,
                confidence_pct=trap_score,
                holding_period='N/A', target_move_pct=0,
                risk_level='HIGH', entry_type='SKIP',
                entry_strike=None, stop_loss_level=0,
                key_reasons=[],
                red_flags=self._get_trap_reasons(ctx, structures)
            )
        
        # Directional conviction
        bull_score = self._bull_signal_strength(ctx, structures)
        bear_score = self._bear_signal_strength(ctx, structures)
        net_direction = bull_score - bear_score
        
        # Determine verdict
        if net_direction > 35 and score > 75:
            verdict = Verdict.STRONG_BUY
            confidence = min(95, 60 + net_direction//2)
            holding = "1-3 DAYS" if vel_z > 2.5 else "INTRADAY"
        elif net_direction > 20 and score > 60:
            verdict = Verdict.BUY_WATCH
            confidence = min(80, 50 + net_direction)
            holding = "1-5 DAYS"
        elif net_direction < -35 and score > 75:
            verdict = Verdict.STRONG_SELL
            confidence = min(95, 60 + abs(net_direction)//2)
            holding = "1-3 DAYS"
        elif net_direction < -20 and score > 60:
            verdict = Verdict.SELL_WATCH
            confidence = min(80, 50 + abs(net_direction))
            holding = "1-5 DAYS"
        else:
            verdict = Verdict.NEUTRAL
            confidence = 40
            holding = "WAIT"
        
        # Determine best entry vehicle
        entry_type, entry_strike = self._recommend_entry(verdict, ctx, structures)
        
        return SmartMoneyVerdict(
            verdict=verdict,
            confidence_pct=confidence,
            holding_period=holding,
            target_move_pct=self._estimate_target(verdict, ctx),
            risk_level=self._assess_risk(ctx),
            entry_type=entry_type,
            entry_strike=entry_strike,
            stop_loss_level=self._compute_stop_loss(verdict, ctx),
            key_reasons=self._get_key_reasons(verdict, ctx, structures),
            red_flags=self._get_red_flags(ctx, structures)
        )
    
    def _compute_trap_score(self, ctx: dict, structures: list) -> int:
        """
        Detect FAKE smart money signals — the most dangerous situation.
        """
        score = 0
        
        # TRAP 1: Short squeeze setup already played out (OI declining after big move)
        if ctx.get('oi_signal') == 'LONG_UNWINDING' and ctx.get('price_change_today', 0) > 3:
            score += 40   # Stock already moved big, now longs exiting = SELL THE NEWS
        
        # TRAP 2: Straddle bought near event = EXPECTS IV CRUSH after event
        straddles = [s for s in structures if s.structure == TradeStructure.STRADDLE]
        if straddles and ctx.get('days_to_expiry', 10) < 2:
            score += 35   # Straddle + near expiry = theta risk
        
        # TRAP 3: Protective hedges being mistaken for bearish signal
        hedges = [s for s in structures if s.structure == TradeStructure.PROTECTIVE_PUT_HEDGE]
        if len(hedges) > 2:
            score += 30   # Multiple hedges = existing longs protecting, NOT new bearish bets
        
        # TRAP 4: OI spike in very illiquid strike (fake signal)
        if ctx.get('atm_distance_pct', 0) > 8:   # Strike >8% away
            score += 25
        
        # TRAP 5: IV Rank very high — option buyers are paying too much
        if ctx.get('iv_rank', 50) > 80:
            score += 20   # Expensive options = bad time to buy naked
        
        return min(100, score)
    
    def _bull_signal_strength(self, ctx: dict, structures: list) -> int:
        score = 0
        # OI Signals
        if ctx.get('oi_signal') == 'LONG_BUILDUP': score += 25
        elif ctx.get('oi_signal') == 'SHORT_COVERING': score += 15
        # GEX
        if ctx.get('gex', 0) < -20_000_000: score += 15   # Negative GEX = explosive potential
        # Structures
        for s in structures:
            if s.directional_bias == 'BULLISH':
                score += {'HIGH':20,'MEDIUM':12,'LOW':6}[s.conviction] * s.confidence
        # FII
        if ctx.get('fii_net_change', 0) > 5000: score += 15
        # Technicals
        if ctx.get('vwap_position') == 'ABOVE': score += 10
        if ctx.get('rsi_14', 50) < 40: score += 8   # Oversold but building
        # VEX: if IV drops, dealers buy → bullish
        if ctx.get('vex', 0) < 0: score += 8
        return score
    
    def _bear_signal_strength(self, ctx: dict, structures: list) -> int:
        score = 0
        if ctx.get('oi_signal') == 'SHORT_BUILDUP': score += 25
        elif ctx.get('oi_signal') == 'LONG_UNWINDING': score += 15
        for s in structures:
            if s.directional_bias == 'BEARISH':
                score += {'HIGH':20,'MEDIUM':12,'LOW':6}[s.conviction] * s.confidence
        if ctx.get('fii_net_change', 0) < -5000: score += 15
        if ctx.get('vwap_position') == 'BELOW': score += 10
        if ctx.get('rsi_14', 50) > 70: score += 8
        return score
    
    def _recommend_entry(self, verdict: Verdict, ctx: dict, structures: list) -> tuple:
        atm = ctx.get('atm_strike', 0)
        iv_rank = ctx.get('iv_rank', 50)
        days_to_expiry = ctx.get('days_to_expiry', 7)
        
        if verdict in [Verdict.STRONG_BUY, Verdict.BUY_WATCH]:
            # Spreads preferred when IV is high (expensive options)
            if iv_rank > 60 or days_to_expiry < 3:
                return "BULL CALL SPREAD", int(atm)   # Limited risk, better R:R
            elif iv_rank < 35:
                return "NAKED CE BUY", int(atm)         # Options cheap = naked buy fine
            else:
                return "STOCK / CE BUY", int(atm)
        elif verdict == Verdict.STRONG_SELL:
            if iv_rank > 60:
                return "BEAR PUT SPREAD", int(atm)
            else:
                return "NAKED PE BUY", int(atm)
        return "WAIT", None
    
    def _estimate_target(self, verdict: Verdict, ctx: dict) -> float:
        atr = ctx.get('atr_14_pct', 2.0)
        if verdict in [Verdict.STRONG_BUY, Verdict.STRONG_SELL]:
            return round(atr * 2.5, 2)
        elif verdict in [Verdict.BUY_WATCH, Verdict.SELL_WATCH]:
            return round(atr * 1.5, 2)
        return 0.0
    
    def _compute_stop_loss(self, verdict: Verdict, ctx: dict) -> float:
        spot = ctx.get('spot_price', 100)
        atr = ctx.get('atr_14_pct', 2.0)
        if verdict in [Verdict.STRONG_BUY, Verdict.BUY_WATCH]:
            return round(spot * (1 - atr/100 * 0.8), 2)
        elif verdict in [Verdict.STRONG_SELL, Verdict.SELL_WATCH]:
            return round(spot * (1 + atr/100 * 0.8), 2)
        return 0.0
    
    def _assess_risk(self, ctx: dict) -> str:
        if ctx.get('gex', 0) < -50_000_000 and ctx.get('iv_rank', 50) < 30:
            return "HIGH REWARD/RISK"
        elif ctx.get('days_to_expiry', 10) < 2:
            return "HIGH (near expiry)"
        return "MEDIUM"
    
    def _get_key_reasons(self, verdict: Verdict, ctx: dict, structures: list) -> list:
        reasons = []
        if ctx.get('oi_signal') in ['LONG_BUILDUP', 'SHORT_COVERING']:
            reasons.append(f"OI: {ctx['oi_signal'].replace('_',' ')} confirms direction")
        if ctx.get('velocity_zscore', 0) > 2:
            reasons.append(f"OI velocity {ctx['velocity_zscore']:.1f}σ above normal — institutional urgency")
        for s in structures[:2]:   # Top 2 structures
            reasons.append(f"Detected: {s.explanation}")
        if ctx.get('fii_net_change', 0) > 0:
            reasons.append(f"FII adding longs: +{ctx['fii_net_change']:,} contracts")
        if ctx.get('gex', 0) < 0:
            reasons.append(f"Negative GEX: dealers forced to amplify any breakout")
        return reasons[:4]
    
    def _get_trap_reasons(self, ctx: dict, structures: list) -> list:
        reasons = []
        if ctx.get('iv_rank', 0) > 80:
            reasons.append(f"IV Rank {ctx['iv_rank']}% — options overpriced, bad time to buy")
        hedges = [s for s in structures if s.structure == TradeStructure.PROTECTIVE_PUT_HEDGE]
        if hedges:
            reasons.append("Put activity is HEDGING by longs, not directional bearish bets")
        straddles = [s for s in structures if s.structure == TradeStructure.STRADDLE]
        if straddles:
            reasons.append("Straddle = uncertainty play, no clear direction signal")
        return reasons
    
    def _get_red_flags(self, ctx: dict, structures: list) -> list:
        flags = []
        if ctx.get('days_to_expiry', 10) < 2:
            flags.append("⚠️ Near expiry — theta decay risk very high")
        if ctx.get('iv_rank', 50) > 70:
            flags.append(f"⚠️ IV Rank {ctx.get('iv_rank')}% — options expensive")
        if ctx.get('pcr', 1.0) > 1.8 or ctx.get('pcr', 1.0) < 0.4:
            flags.append("⚠️ PCR extreme — possible contrarian reversal zone")
        return flags
```

---

## 🆕 MODULE 9: PRIORITY WATCHLIST SYSTEM (TOP 25)

### Architecture

```python
class WatchlistManager:
    """
    Two-tier scanning:
    - Tier 1 (Priority 25): Scan every 1 min, full analysis, immediate alerts
    - Tier 2 (All 150+): Scan every 3 min, standard analysis
    """
    
    def __init__(self):
        self.priority_stocks: list[WatchlistEntry] = []  # Max 25
        self.all_fno_stocks: list[str] = self._load_all_fno()
    
    def load_from_db(self):
        """Loads user's saved watchlist from SQLite"""
        with sqlite3.connect('watchlist.db') as conn:
            rows = conn.execute(
                "SELECT symbol, added_at, notes, alert_settings FROM watchlist ORDER BY priority"
            ).fetchall()
            self.priority_stocks = [WatchlistEntry(*r) for r in rows]
    
    def add_stock(self, symbol: str, notes: str = "", alert_config: dict = None):
        if len(self.priority_stocks) >= 25:
            raise ValueError("Watchlist full (max 25). Remove a stock first.")
        if symbol not in self.all_fno_stocks:
            raise ValueError(f"{symbol} is not in F&O list")
        entry = WatchlistEntry(
            symbol=symbol, added_at=datetime.now(),
            notes=notes,
            alert_settings=alert_config or DEFAULT_ALERT_CONFIG
        )
        with sqlite3.connect('watchlist.db') as conn:
            conn.execute(
                "INSERT INTO watchlist VALUES (?,?,?,?)",
                (symbol, entry.added_at, notes, json.dumps(alert_config))
            )
        self.priority_stocks.append(entry)
    
    def get_scan_schedule(self) -> dict:
        return {
            'priority': {
                'symbols': [e.symbol for e in self.priority_stocks],
                'interval_seconds': 60,      # Every 60 seconds for priority
                'full_analysis': True,
                'alert_on_any_signal': True
            },
            'standard': {
                'symbols': self.all_fno_stocks,
                'interval_seconds': 180,     # Every 3 minutes
                'full_analysis': True,
                'alert_on_high_score_only': True  # Only alert score > 75
            }
        }
    
    def get_priority_boost(self, symbol: str) -> float:
        """Priority stocks get score boosted by 10% for ranking"""
        return 1.10 if symbol in [e.symbol for e in self.priority_stocks] else 1.0


@dataclass
class WatchlistEntry:
    symbol: str
    added_at: datetime
    notes: str
    alert_settings: dict

DEFAULT_ALERT_CONFIG = {
    'oi_velocity_threshold': 1.5,    # Alert when z-score > this
    'score_threshold': 65,           # Alert when score crosses this
    'structures_to_alert': ['NAKED_CALL_BUY', 'NAKED_PUT_BUY', 'BULL_CALL_SPREAD', 'BEARISH_CALL_WRITE'],
    'verdict_to_alert': ['STRONG_BUY', 'STRONG_SELL'],
    'telegram_instant': True,        # Immediate Telegram vs batched
}
```

### Watchlist API Endpoints
```
POST   /api/watchlist/add           → Add stock {symbol, notes, alert_config}
DELETE /api/watchlist/{symbol}      → Remove stock
GET    /api/watchlist               → Get all 25 + their current metrics
GET    /api/watchlist/{symbol}      → Deep analysis for one watchlist stock
PUT    /api/watchlist/{symbol}      → Update notes/alert config
GET    /api/watchlist/verdicts      → Latest verdicts for all 25 priority stocks
```

---

## 🆕 MODULE 10: TELEGRAM ALERT SYSTEM

### Architecture Overview
```
Alert Engine (Python) → Redis Pub/Sub → TelegramBotWorker → Telegram Bot API → Your Phone
                     ↓
              Alert Deduplication (Redis TTL)
              Alert Rate Limiting (max 5/min)
              Alert Priority Queue (P1 > P2 > P3)
```

### Full Implementation

```python
# telegram_bot.py
import asyncio
import redis.asyncio as aioredis
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from datetime import datetime
import json

TELEGRAM_TOKEN = "your_bot_token_here"   # From @BotFather
ALLOWED_CHAT_IDS = [123456789]           # Your Telegram user ID (security)

class FNOAlertBot:
    
    def __init__(self):
        self.redis = aioredis.Redis(host='localhost', port=6379, decode_responses=True)
        self.bot = Bot(token=TELEGRAM_TOKEN)
        self.dedup_cache = {}             # {alert_key: last_sent_timestamp}
        self.COOLDOWN_MINUTES = {
            'P1': 5,    # Critical alerts repeat max once every 5 min
            'P2': 15,   # Standard alerts max once per 15 min
            'P3': 60,   # Low priority max once per hour
        }
    
    async def run(self):
        """Main loop: consumes from Redis pub/sub and sends alerts"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe('fno:alerts')
        async for msg in pubsub.listen():
            if msg['type'] == 'message':
                alert = json.loads(msg['data'])
                await self.process_alert(alert)
    
    async def process_alert(self, alert: dict):
        """Rate limiting + dedup before sending"""
        key = f"{alert['symbol']}:{alert['signal_type']}"
        priority = alert.get('priority', 'P2')
        cooldown = self.COOLDOWN_MINUTES[priority] * 60
        
        last_sent = self.dedup_cache.get(key, 0)
        if (datetime.now().timestamp() - last_sent) < cooldown:
            return   # Duplicate within cooldown, skip
        
        self.dedup_cache[key] = datetime.now().timestamp()
        await self.send_alert(alert)
    
    async def send_alert(self, alert: dict):
        """Format and send the alert message"""
        text = self._format_alert(alert)
        keyboard = self._build_keyboard(alert)
        
        for chat_id in ALLOWED_CHAT_IDS:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=keyboard
            )
    
    def _format_alert(self, alert: dict) -> str:
        """
        Rich Telegram message format with all key data
        """
        sym = alert['symbol']
        verdict = alert.get('verdict', 'SIGNAL')
        price = alert.get('price', 0)
        signal = alert.get('signal_type', '')
        structure = alert.get('structure', '')
        velocity = alert.get('velocity_zscore', 0)
        score = alert.get('momentum_score', 0)
        entry = alert.get('entry_type', '')
        entry_strike = alert.get('entry_strike', '')
        stop = alert.get('stop_loss', 0)
        target_pct = alert.get('target_pct', 0)
        is_priority = alert.get('is_watchlist', False)
        
        # Priority badge
        wl_tag = "⭐ *WATCHLIST PRIORITY*\n" if is_priority else ""
        
        # Verdict emoji
        v_emoji = {
            'STRONG_BUY': '⚡🟢', 'BUY_WATCH': '🟢',
            'STRONG_SELL': '⚡🔴', 'SELL_WATCH': '🔴',
            'TRAP_WARNING': '⚠️', 'NEUTRAL': '🟡'
        }.get(verdict, '📊')
        
        reasons_text = ""
        if alert.get('key_reasons'):
            reasons_text = "\n*Why:*\n" + "\n".join(f"• {r}" for r in alert['key_reasons'][:3])
        
        red_flags_text = ""
        if alert.get('red_flags'):
            red_flags_text = "\n*⚠️ Red Flags:*\n" + "\n".join(f"• {r}" for r in alert['red_flags'][:2])
        
        return f"""
{wl_tag}
{v_emoji} *{sym}* — {verdict.replace('_', ' ')}
━━━━━━━━━━━━━━
💰 Price: ₹{price:,.2f}
📊 Score: {score}/100
🔄 Signal: {signal.replace('_', ' ')}
🏗️ Structure: {structure.replace('_', ' ') if structure else 'N/A'}
⚡ OI Velocity: {velocity:.1f}σ

*Recommended Entry:*
→ {entry} {f'@ {entry_strike}' if entry_strike else ''}
→ Stop: ₹{stop:,.2f}
→ Target: +{target_pct:.1f}%
{reasons_text}
{red_flags_text}
━━━━━━━━━━━━━━
🕐 {datetime.now().strftime('%H:%M:%S IST')}
""".strip()
    
    def _build_keyboard(self, alert: dict) -> InlineKeyboardMarkup:
        sym = alert['symbol']
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Full Analysis", callback_data=f"analysis:{sym}"),
                InlineKeyboardButton("🔕 Mute 1hr", callback_data=f"mute:{sym}:60"),
            ],
            [
                InlineKeyboardButton("⭐ Add to Watchlist", callback_data=f"watchlist:add:{sym}"),
                InlineKeyboardButton("❌ Remove Watchlist", callback_data=f"watchlist:remove:{sym}"),
            ]
        ])


# telegram_commands.py — Bot commands for two-way interaction
class FNOBotCommands:
    """
    Commands available in Telegram:
    /scan         → Top 10 by score right now
    /watchlist    → Your 25 priority stocks + current verdicts
    /add SYMBOL   → Add stock to watchlist
    /remove SYM   → Remove from watchlist
    /stock SYM    → Full analysis for any FNO stock
    /alerts       → Show/manage your alert settings
    /mute SYM 60  → Mute alerts for SYMBOL for 60 minutes
    /today        → Today's triggered alerts summary
    /gex          → Market-wide GEX regime
    """
    
    async def cmd_watchlist(self, update: Update, context):
        wl = await self.api_client.get('/api/watchlist/verdicts')
        lines = ["*⭐ YOUR WATCHLIST — CURRENT VERDICTS*\n━━━━━━━━━━━━━━"]
        for stock in wl:
            v = stock['verdict']
            emoji = {'STRONG_BUY':'⚡🟢','BUY_WATCH':'🟢','STRONG_SELL':'⚡🔴',
                     'SELL_WATCH':'🔴','NEUTRAL':'🟡','TRAP_WARNING':'⚠️'}.get(v,'📊')
            lines.append(f"{emoji} *{stock['symbol']}* ₹{stock['price']:,} | {v.replace('_',' ')} | Score:{stock['score']}")
        await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.MARKDOWN_V2)
    
    async def cmd_stock(self, update: Update, context):
        sym = context.args[0].upper() if context.args else None
        if not sym:
            await update.message.reply_text("Usage: /stock RELIANCE")
            return
        data = await self.api_client.get(f'/api/stock/{sym}/snapshot')
        # Format and send full analysis card
        ...
    
    async def cmd_scan(self, update: Update, context):
        top = await self.api_client.get('/api/scanner?limit=10')
        lines = ["*🔥 TOP 10 RIGHT NOW*\n━━━━━━━━━━━━━━"]
        for i, s in enumerate(top, 1):
            lines.append(f"{i}. *{s['symbol']}* {s['verdict_emoji']} Score:{s['score']} | {s['oi_signal']}")
        await update.message.reply_text('\n'.join(lines), parse_mode=ParseMode.MARKDOWN_V2)
```

### Alert Priority Rules
```python
ALERT_RULES = [
    # P1 — Instant, watchlist stocks
    {'priority': 'P1', 'condition': lambda ctx: 
        ctx['is_watchlist'] and ctx['verdict'] in ['STRONG_BUY', 'STRONG_SELL'],
     'cooldown_min': 5},
    
    # P1 — Extreme OI velocity
    {'priority': 'P1', 'condition': lambda ctx:
        ctx['velocity_zscore'] > 3.0,
     'cooldown_min': 5},
    
    # P1 — Gamma flip (regime change)
    {'priority': 'P1', 'condition': lambda ctx:
        ctx['gex_just_crossed_zero'],
     'cooldown_min': 10},
    
    # P2 — Watchlist normal signals
    {'priority': 'P2', 'condition': lambda ctx:
        ctx['is_watchlist'] and ctx['score'] > 65,
     'cooldown_min': 15},
    
    # P2 — Any stock, extreme naked buy/sell detected
    {'priority': 'P2', 'condition': lambda ctx:
        any(s.structure in [TradeStructure.NAKED_CALL_BUY, TradeStructure.NAKED_PUT_BUY]
            and s.confidence > 0.8 and ctx['velocity_zscore'] > 2.0
            for s in ctx['structures']),
     'cooldown_min': 15},
    
    # P3 — General scanner alerts
    {'priority': 'P3', 'condition': lambda ctx:
        ctx['score'] > 80 and not ctx['is_watchlist'],
     'cooldown_min': 60},
]
```

### Telegram Bot Setup Guide
```
1. Message @BotFather on Telegram → /newbot → Save token
2. Get your Chat ID: message @userinfobot
3. Add to .env:
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
4. Install: pip install python-telegram-bot==20.x --break-system-packages
5. Start bot worker: python -m app.telegram.bot_worker
6. Docker service: add to docker-compose.yml
```

---

## 🔬 ADVANCED TECHNICAL EDGE — WHAT NO ONE ELSE DOES

### Edge 1: OIWAP (OI-Weighted Average Price)
```python
def compute_oiwap(option_chain_history: list) -> float:
    """
    Like VWAP but weights price by OI change (not volume).
    Shows: 'At what price level did the most NEW positions open today?'
    If LTP > OIWAP: longs above their average entry → COMFORTABLE
    If LTP < OIWAP: longs underwater → FORCED SELLING risk
    """
    numerator = sum(snap.price * abs(snap.oi_change) for snap in option_chain_history)
    denominator = sum(abs(snap.oi_change) for snap in option_chain_history)
    return numerator / max(denominator, 1)
```

### Edge 2: Cumulative Delta of OI (CDI)
```python
def compute_cdi(history: list) -> pd.Series:
    """
    Call-Put OI imbalance accumulated over the day.
    CDI Rising + Price Rising = Smart money loading calls → TREND DAY
    CDI Falling + Price Rising = Divergence → POTENTIAL REVERSAL
    This is the options equivalent of CVD (Cumulative Volume Delta) in futures.
    """
    cdi_values = []
    running = 0
    for snap in history:
        call_pressure = snap.call_oi_change * snap.call_delta   # Δ-weighted call demand
        put_pressure = -snap.put_oi_change * snap.put_delta     # Δ-weighted put demand
        running += call_pressure + put_pressure
        cdi_values.append(running)
    return pd.Series(cdi_values, name='CDI')
```

### Edge 3: Put-Call OI Ratio by Moneyness Zone
```python
def pcr_by_zone(option_chain: pd.DataFrame, spot: float) -> dict:
    """
    Overall PCR is too noisy. Segment by zone:
    - Deep OTM: hedgers & tail-risk buyers
    - Near OTM (1-3%): directional players
    - ATM: market makers & short-term speculators
    - ITM: stock replacement (institutions)
    
    Near-OTM PCR is the BEST directional signal.
    Deep-OTM PCR is a FEAR gauge.
    """
    zones = {'deep_otm':[], 'near_otm':[], 'atm':[], 'itm':[]}
    for _, row in option_chain.iterrows():
        dist = abs(row.strike - spot) / spot * 100
        zone = 'deep_otm' if dist>5 else 'near_otm' if dist>1.5 else 'atm' if dist<1.5 else 'itm'
        zones[zone].append(row)
    
    return {
        zone: (sum(r.put_oi for r in rows) / max(sum(r.call_oi for r in rows), 1))
        for zone, rows in zones.items()
    }
```

### Edge 4: Strike Pinning Probability (Expiry Week)
```python
def pinning_probability(spot: float, max_pain: float, 
                        gex_at_atm: float, days_to_expiry: int) -> float:
    """
    Options market makers actively defend max pain near expiry.
    High GEX at ATM = strong dealer interest in keeping price pinned.
    This signal predicts: price likely to gravitate back to max_pain by EOD.
    Use case: Avoid buying calls/puts when pinning probability > 0.65.
    """
    distance = abs(spot - max_pain) / spot
    gex_factor = min(1.0, abs(gex_at_atm) / 50_000_000)
    time_factor = max(0, (5 - days_to_expiry) / 5)  # Peaks on expiry day
    
    base_prob = 0.35 + (gex_factor * 0.35) + (time_factor * 0.30)
    distance_penalty = distance * 2  # Farther = harder to pin
    
    return max(0, min(1.0, base_prob - distance_penalty))
```

### Edge 5: FII Expiry Rollover Detector
```python
def detect_fii_rollover(current_oi: dict, prev_month_oi: dict, days_to_expiry: int) -> dict:
    """
    FIIs roll their huge positions 3-5 days before expiry.
    When they roll: near-month OI drops + next-month OI rises simultaneously.
    This is NOT a bearish signal — just mechanical rolling.
    TRAP: Many retail traders misread FII rollover as "institutions are selling".
    """
    near_month_oi = current_oi.get('near', 0)
    next_month_oi = current_oi.get('next', 0)
    prev_near = prev_month_oi.get('near', 0)
    
    rollover_pct = (prev_near - near_month_oi) / max(prev_near, 1) * 100
    
    if days_to_expiry <= 5 and rollover_pct > 15:
        return {
            'rolling': True,
            'pct_rolled': rollover_pct,
            'warning': "FII ROLLOVER IN PROGRESS — Do not interpret near-month OI drop as bearish"
        }
    return {'rolling': False}
```

### Edge 6: Volatility Skew Signal
```python
def skew_signal(option_chain: pd.DataFrame, spot: float) -> dict:
    """
    Put skew (OTM puts more expensive than OTM calls) = fear premium.
    Call skew (OTM calls more expensive) = euphoria / squeeze potential.
    
    Skew CHANGE over time is more useful than absolute skew.
    If put skew FALLING while price stagnant → smart money buying calls → bullish
    """
    otm_call_iv = option_chain[
        (option_chain.option_type == 'CE') & 
        (option_chain.strike.between(spot*1.02, spot*1.05))
    ]['iv'].mean()
    
    otm_put_iv = option_chain[
        (option_chain.option_type == 'PE') &
        (option_chain.strike.between(spot*0.95, spot*0.98))
    ]['iv'].mean()
    
    skew = otm_put_iv - otm_call_iv   # Positive = put skew (fear), Negative = call skew (bullish)
    
    signal = 'EXTREME_FEAR' if skew > 8 else 'FEAR' if skew > 4 else \
             'NEUTRAL' if abs(skew) < 2 else 'CALL_SKEW' if skew < -2 else 'MILD_FEAR'
    
    return {'skew': skew, 'signal': signal, 'otm_call_iv': otm_call_iv, 'otm_put_iv': otm_put_iv}
```

---

## 📱 ENHANCED FRONTEND PAGES

### New Page: Priority Watchlist Dashboard
```
┌─────────────────────────────────────────────────────────────────────┐
│  ⭐ YOUR PRIORITY WATCHLIST (25 stocks)              [+ Add Stock]  │
├─────────────────────────────────────────────────────────────────────┤
│  SYMBOL │ PRICE  │ VERDICT        │ STRUCTURE       │ ENTRY       │
├─────────┼────────┼────────────────┼─────────────────┼─────────────┤
│RELIANCE │ ₹2847  │⚡🟢 STRONG BUY │ NAKED CALL BUY  │ CE @ 2860  │
│TATASTEEL│ ₹148   │🟢  BUY WATCH   │ BULL CALL SPREAD│ 150/155 CS │
│INFY     │ ₹1724  │🟡  NEUTRAL     │ Put WRITER (↑)  │ WAIT       │
│SBIN     │ ₹824   │🔴  SELL WATCH  │ SHORT BUILDUP   │ PE @ 820   │
└─────────┴────────┴────────────────┴─────────────────┴─────────────┘
```

### Enhanced Stock Drill-Down — New Panels

1. **OI Velocity Panel**
   - Real-time velocity speedometer (like RPM gauge)
   - Z-score bar with normal/unusual/extreme zones
   - Velocity history line chart (acceleration visible)

2. **Trade Structure Panel**
   - Card for each detected structure with confidence %
   - Visual diagram of spread if detected (buy leg / sell leg)
   - "What smart money is doing" plain-English explanation

3. **Smart Money Verdict Card**
   - Big verdict badge at top
   - Specific entry: instrument + strike
   - Target % and stop loss level
   - Reasons list + red flags list

4. **Skew + PCR Zone Chart**
   - PCR broken by moneyness zone (not just overall PCR)
   - Volatility skew chart (call IV vs put IV by strike)
   - OIWAP level on price chart

---

## 🗄️ DATABASE SCHEMA ADDITIONS

```sql
-- Watchlist table (persistent, user-managed)
CREATE TABLE priority_watchlist (
    symbol          TEXT PRIMARY KEY,
    added_at        TIMESTAMPTZ DEFAULT NOW(),
    notes           TEXT,
    alert_config    JSONB,
    sort_order      INTEGER DEFAULT 0
);

-- Trade structure detections log
CREATE TABLE structure_detections (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT NOT NULL,
    structure_type  TEXT NOT NULL,
    confidence      NUMERIC,
    buy_leg_strike  NUMERIC,
    sell_leg_strike NUMERIC,
    net_premium     TEXT,   -- DEBIT/CREDIT
    directional_bias TEXT,
    conviction      TEXT,
    explanation     TEXT
);
SELECT create_hypertable('structure_detections', 'time');

-- Smart money verdicts log
CREATE TABLE smart_money_verdicts (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT NOT NULL,
    verdict         TEXT,
    confidence_pct  INTEGER,
    holding_period  TEXT,
    entry_type      TEXT,
    entry_strike    NUMERIC,
    stop_loss       NUMERIC,
    target_pct      NUMERIC,
    key_reasons     JSONB,
    red_flags       JSONB
);
SELECT create_hypertable('smart_money_verdicts', 'time');

-- OI Velocity snapshots
CREATE TABLE oi_velocity_log (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT,
    strike          NUMERIC,
    option_type     CHAR(2),
    velocity_3min   NUMERIC,   -- OI change / min (3min window)
    velocity_15min  NUMERIC,
    velocity_30min  NUMERIC,
    velocity_zscore NUMERIC,
    acceleration    NUMERIC,
    vol_oi_ratio    NUMERIC,
    freshness_class TEXT       -- EXTREME_FRESH/MOSTLY_FRESH/MIXED/MOSTLY_CLOSING
);
SELECT create_hypertable('oi_velocity_log', 'time');

-- Telegram alert log (for dedup and history)
CREATE TABLE telegram_alerts_sent (
    id              SERIAL PRIMARY KEY,
    sent_at         TIMESTAMPTZ DEFAULT NOW(),
    symbol          TEXT,
    signal_type     TEXT,
    priority        TEXT,
    verdict         TEXT,
    message_preview TEXT
);
```

---

## 🚦 COMPLETE SIGNAL PRIORITY MATRIX

| Signal | Priority | Watchlist Boost | Telegram Timing |
|--------|----------|-----------------|-----------------|
| STRONG BUY + Naked Call + Vel>3σ | P1 | Immediate | Instant |
| STRONG SELL + Naked Put + Vel>3σ | P1 | Immediate | Instant |
| GEX Gamma Flip | P1 | Immediate | Instant |
| Straddle + event tomorrow | P1 | Yes | Instant |
| Bull Call Spread detected + LONG BUILDUP | P2 | Priority | <5min |
| Short Covering + Put Wall holding | P2 | Priority | <5min |
| PCR Zone (near-OTM) <0.4 or >1.8 | P2 | Yes | <5min |
| Call Writer at resistance | P2 | Yes | <15min |
| Score>80 any stock | P3 | No | Batched hourly |
| FII rollover starting (expiry-5 days) | P3 | No | Daily digest |
| Max Pain distance >5% | P3 | No | Batched |

---

## 🏗️ UPDATED SYSTEM ARCHITECTURE (V2)

```
                          NSE API (Option Chain, 3min)
                          Broker WebSocket (Fyers/Upstox, live)
                                    │
                          ┌─────────▼──────────┐
                          │  Data Ingestion    │
                          │  + Redis Queue     │
                          └─────────┬──────────┘
                                    │ batched per symbol
              ┌─────────────────────▼─────────────────────┐
              │            COMPUTATION ENGINE              │
              │                                           │
              │  ┌─────────┐  ┌──────────┐  ┌─────────┐ │
              │  │ Greeks  │  │ Velocity │  │Structure│ │
              │  │ Engine  │  │ Engine   │  │Detector │ │
              │  └────┬────┘  └────┬─────┘  └────┬────┘ │
              │       └────────────┼──────────────┘      │
              │              ┌─────▼─────┐               │
              │              │ Verdict   │               │
              │              │  Engine   │               │
              │              └─────┬─────┘               │
              └────────────────────┼─────────────────────┘
                                   │
              ┌────────────────────▼──────────────────────┐
              │              ALERT ENGINE                  │
              │   Priority Router → Dedup → Rate Limit    │
              └────────┬──────────────────┬───────────────┘
                       │                  │
              ┌────────▼──────┐  ┌────────▼───────┐
              │ FastAPI WS    │  │ Telegram Worker │
              │ (Frontend)    │  │ (Your Phone)    │
              └───────────────┘  └────────────────┘
```

---

## 📦 DOCKER COMPOSE

```yaml
version: '3.9'
services:
  backend:
    build: ./backend
    ports: ['8000:8000']
    env_file: .env
    depends_on: [timescaledb, redis]
    
  celery_worker:
    build: ./backend
    command: celery -A app.tasks worker --concurrency=8
    depends_on: [redis]
    
  celery_beat:
    build: ./backend
    command: celery -A app.tasks beat
    depends_on: [redis]
    
  telegram_bot:
    build: ./backend
    command: python -m app.telegram.bot_worker
    env_file: .env
    depends_on: [redis, backend]
    
  frontend:
    build: ./frontend
    ports: ['3000:80']
    
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_PASSWORD: fno_secret
      POSTGRES_DB: fno_monitor
    volumes: ['pgdata:/var/lib/postgresql/data']
    ports: ['5432:5432']
    
  redis:
    image: redis:7-alpine
    ports: ['6379:6379']
    
volumes:
  pgdata:
```

---

## 🗺️ UPDATED DEVELOPMENT ROADMAP (V2)

### Phase 1 — Core (Week 1-2)
- [ ] Data ingestion for 150+ FNO stocks
- [ ] Black-76 greeks engine  
- [ ] Basic OI signals
- [ ] TimescaleDB + FastAPI skeleton

### Phase 2 — Velocity + Structure (Week 3-4) ← NEW
- [ ] OI Velocity Engine with z-score
- [ ] Trade Structure Identifier (naked vs spread)
- [ ] OIWAP computation
- [ ] Cumulative Delta of OI (CDI)
- [ ] Skew analysis per strike

### Phase 3 — Intelligence (Week 5-6)
- [ ] GEX/DEX/VEX/CEX dealer exposure
- [ ] Smart Money Verdict Engine
- [ ] Trap detection module
- [ ] Pinning probability (expiry week)

### Phase 4 — Watchlist + Telegram (Week 7) ← NEW
- [ ] Priority Watchlist (25 stocks) CRUD
- [ ] Differential scan frequency (1min vs 3min)
- [ ] Telegram bot + commands
- [ ] Alert priority matrix + dedup + rate limiting

### Phase 5 — Frontend V2 (Week 8-9)
- [ ] Velocity gauges + acceleration charts
- [ ] Trade structure detection cards
- [ ] Verdict cards with entry recommendations
- [ ] Watchlist dashboard page
- [ ] PCR zone breakdown chart
- [ ] Skew visualization

### Phase 6 — Production (Week 10)
- [ ] Docker Compose one-command setup
- [ ] Performance: 150 stocks × 60s for priority, 180s standard
- [ ] Backtesting: did velocity+structure signals work historically?
- [ ] Alert fatigue prevention (smart cooldowns)
```
