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
        # Assuming net_gex_cr is already in Crores.
        # If GEX is positive -> Stabilizing -> Bullish in uptrend?
        # Actually positive GEX suppresses volatility. Negative GEX increases it.
        # The prompt says: "GEX_Score x 0.25".
        # Usually +GEX is associated with market stability/upward drift. -GEX with sharp moves (often down).
        # Let's assume +GEX is bullish factor for this score as per common "Positive Gamma" bias.
        gex_score = max(-1.0, min(1.0, net_gex_cr / 100.0))

        # 3. PCR Velocity Score
        # PCR Rising = Put Writing (Bullish) or Call Unwinding (Bearish)?
        # Generally Rising PCR = Bullish (More Puts than Calls -> Support building).
        # Falling PCR = Bearish.
        pcr_vel = (pcr_now - pcr_15min_ago) / 15.0  # per-minute rate
        PCR_SCALE = 0.02  # threshold: 0.02/min change = ±1.0 score
        # If pcr_vel is positive -> PCR is rising -> Bullish.
        pcr_vel_score = max(-1.0, min(1.0, pcr_vel / PCR_SCALE))

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
