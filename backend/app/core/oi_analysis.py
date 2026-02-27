# backend/app/core/oi_analysis.py

import numpy as np
from dataclasses import dataclass
from collections import deque
from enum import Enum
from typing import List, Dict, Optional, Tuple

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
        # Rolling window of (timestamp, oi, volume) tuples — 60 snapshots = 3hr at 3min intervals
        self.history: deque = deque(maxlen=60)

    def add_snapshot(self, snapshot: OISnapshot):
        self.history.append((snapshot.timestamp, snapshot.oi, snapshot.volume))

    def velocity(self, window_minutes: int = 15) -> float:
        """OI change per minute over last N minutes"""
        if len(self.history) < 2:
            return 0.0

        # Approximate window bars (assuming 3 min interval, adjust as needed)
        window_bars = max(1, window_minutes // 3)
        recent = list(self.history)[-min(window_bars + 1, len(self.history)):]

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
        if not self.history:
             return "UNKNOWN"
        recent = list(self.history)[-1]
        current_oi = recent[1]
        current_vol = recent[2]
        ratio = current_vol / max(current_oi, 1)
        if ratio > 1.2:    return "EXTREME_FRESH"   # Very rare — nearly all fresh
        elif ratio > 0.6:  return "MOSTLY_FRESH"    # Unusual — smart money entering
        elif ratio > 0.3:  return "MIXED"           # Normal activity
        else:              return "MOSTLY_CLOSING"  # Low conviction

    def _compute_rolling_velocities(self, window: int = 5) -> list:
        hist = list(self.history)
        velocities = []
        # Need at least window + 1 points to compute velocity over window
        if len(hist) <= window:
             return []

        for i in range(window, len(hist)):
            delta_oi = hist[i][1] - hist[i-window][1]
            delta_t = (hist[i][0] - hist[i-window][0]) / 60
            velocities.append(delta_oi / max(delta_t, 1))
        return velocities

    def _velocity_at_offset(self, offset_bars: int, window_bars: int) -> float:
        hist = list(self.history)
        end_idx = len(hist) - offset_bars
        start_idx = max(0, end_idx - window_bars)

        if end_idx <= 0 or start_idx >= end_idx:
            return 0.0

        # Ensure indices are within bounds
        if end_idx >= len(hist): end_idx = len(hist) - 1

        delta_oi = hist[end_idx][1] - hist[start_idx][1]
        delta_t = (hist[end_idx][0] - hist[start_idx][0]) / 60
        return delta_oi / max(delta_t, 1)


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
        velocity_scores: dict = None    # {(strike, type): velocity_score}
    ) -> List[StructureDetection]:

        detections = []

        # Step 1: Find all strikes with statistically significant OI change
        significant = self._filter_significant(oi_changes)

        if not significant:
            return []

        # Step 2: Find correlated pairs (spread legs)
        spread_pairs = self._find_correlated_pairs(significant, oi_changes)

        # Step 3: Classify each pair or solo
        processed_strikes = set()

        for pair in spread_pairs:
            det = self._classify_spread(pair, oi_changes, atm_strike, price_change)
            if det:
                detections.append(det)
                (s1, t1), (s2, t2) = pair
                processed_strikes.add((s1, t1))
                processed_strikes.add((s2, t2))

        # Step 4: Remaining solo OI changes = naked positions
        for strike_type, change in significant.items():
            if strike_type not in processed_strikes:
                det = self._classify_naked(strike_type, change, oi_changes,
                                          atm_strike, price_change, lot_size)
                if det:
                    detections.append(det)

        return detections

    def _filter_significant(self, oi_changes: dict, threshold_pct: float = 30) -> dict:
        """Keep only strikes with OI change > threshold% of their current OI or absolute min change"""
        # Simplified: check absolute change > 500 contracts for now
        return {k: v for k, v in oi_changes.items()
                if abs(v) > 500  # minimum 500 contracts
                and v != 0}

    def _find_correlated_pairs(self, significant: dict, oi_changes: dict) -> list:
        """
        If two call strikes BOTH gain OI in same 3min window = spread signal.
        Rule: Both same direction change within reasonable distance = spread pair.
        """
        pairs = []
        strikes = list(significant.keys())

        for i, (s1, t1) in enumerate(strikes):
            for j in range(i + 1, len(strikes)):
                (s2, t2) = strikes[j]
                change1 = oi_changes.get((s1,t1), 0)
                change2 = oi_changes.get((s2,t2), 0)

                # Same option type (both CE or both PE) = likely spread
                same_type = t1 == t2
                # Both positive OI change = both legs being bought/sold together
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
