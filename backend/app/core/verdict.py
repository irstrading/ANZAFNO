# backend/app/core/verdict.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List
from .oi_analysis import TradeStructure, StructureDetection

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
    key_reasons: List[str]       # Max 4 bullet points
    red_flags: List[str]         # Reasons to be cautious

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
          - momentum_score
        """
        score = ctx.get('momentum_score', 0)
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
            confidence = min(95, 60 + int(net_direction//2))
            holding = "1-3 DAYS" if vel_z > 2.5 else "INTRADAY"
        elif net_direction > 20 and score > 60:
            verdict = Verdict.BUY_WATCH
            confidence = min(80, 50 + int(net_direction))
            holding = "1-5 DAYS"
        elif net_direction < -35 and score > 75:
            verdict = Verdict.STRONG_SELL
            confidence = min(95, 60 + abs(int(net_direction))//2)
            holding = "1-3 DAYS"
        elif net_direction < -20 and score > 60:
            verdict = Verdict.SELL_WATCH
            confidence = min(80, 50 + abs(int(net_direction)))
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

    def _compute_trap_score(self, ctx: dict, structures: List[StructureDetection]) -> int:
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

    def _bull_signal_strength(self, ctx: dict, structures: List[StructureDetection]) -> int:
        score = 0
        # OI Signals
        if ctx.get('oi_signal') == 'LONG_BUILDUP': score += 25
        elif ctx.get('oi_signal') == 'SHORT_COVERING': score += 15
        # GEX
        if ctx.get('gex', 0) < -20_000_000: score += 15   # Negative GEX = explosive potential
        # Structures
        for s in structures:
            if s.directional_bias == 'BULLISH':
                # Simplified confidence multiplier
                score += {'HIGH':20,'MEDIUM':12,'LOW':6}.get(s.conviction, 10) * s.confidence
        # FII
        if ctx.get('fii_net_change', 0) > 5000: score += 15
        # Technicals
        if ctx.get('vwap_position') == 'ABOVE': score += 10
        if ctx.get('rsi_14', 50) < 40: score += 8   # Oversold but building
        # VEX: if IV drops, dealers buy → bullish
        if ctx.get('vex', 0) < 0: score += 8
        return int(score)

    def _bear_signal_strength(self, ctx: dict, structures: List[StructureDetection]) -> int:
        score = 0
        if ctx.get('oi_signal') == 'SHORT_BUILDUP': score += 25
        elif ctx.get('oi_signal') == 'LONG_UNWINDING': score += 15
        for s in structures:
            if s.directional_bias == 'BEARISH':
                 score += {'HIGH':20,'MEDIUM':12,'LOW':6}.get(s.conviction, 10) * s.confidence
        if ctx.get('fii_net_change', 0) < -5000: score += 15
        if ctx.get('vwap_position') == 'BELOW': score += 10
        if ctx.get('rsi_14', 50) > 70: score += 8
        return int(score)

    def _recommend_entry(self, verdict: Verdict, ctx: dict, structures: List[StructureDetection]) -> tuple:
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

    def _get_key_reasons(self, verdict: Verdict, ctx: dict, structures: List[StructureDetection]) -> List[str]:
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

    def _get_trap_reasons(self, ctx: dict, structures: List[StructureDetection]) -> List[str]:
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

    def _get_red_flags(self, ctx: dict, structures: List[StructureDetection]) -> List[str]:
        flags = []
        if ctx.get('days_to_expiry', 10) < 2:
            flags.append("⚠️ Near expiry — theta decay risk very high")
        if ctx.get('iv_rank', 50) > 70:
            flags.append(f"⚠️ IV Rank {ctx.get('iv_rank')}% — options expensive")
        if ctx.get('pcr', 1.0) > 1.8 or ctx.get('pcr', 1.0) < 0.4:
            flags.append("⚠️ PCR extreme — possible contrarian reversal zone")
        return flags
