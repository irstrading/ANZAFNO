from typing import Dict, Any, List
from enum import Enum
import pandas as pd

class Sentiment(Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    LONG_BUILDUP = "LONG_BUILDUP"
    SHORT_COVERING = "SHORT_COVERING"
    SHORT_BUILDUP = "SHORT_BUILDUP"
    LONG_UNWINDING = "LONG_UNWINDING"

class OIAnalyzer:
    """
    Analyzes Option Chain data for Open Interest (OI) buildup, Support/Resistance, and Sentiment.
    """

    def analyze_buildup(self, ltp_change: float, oi_change: float) -> Sentiment:
        """
        Determine buildup type based on Price Change and OI Change.
        """
        if ltp_change > 0 and oi_change > 0:
            return Sentiment.LONG_BUILDUP
        elif ltp_change > 0 and oi_change < 0:
            return Sentiment.SHORT_COVERING
        elif ltp_change < 0 and oi_change > 0:
            return Sentiment.SHORT_BUILDUP
        elif ltp_change < 0 and oi_change < 0:
            return Sentiment.LONG_UNWINDING
        return Sentiment.NEUTRAL

    def calculate_pcr(self, option_chain: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate Put-Call Ratio (PCR) based on OI and Volume.
        """
        total_ce_oi = option_chain[option_chain['option_type'] == 'CE']['oi'].sum()
        total_pe_oi = option_chain[option_chain['option_type'] == 'PE']['oi'].sum()

        total_ce_vol = option_chain[option_chain['option_type'] == 'CE']['volume'].sum()
        total_pe_vol = option_chain[option_chain['option_type'] == 'PE']['volume'].sum()

        pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
        pcr_vol = total_pe_vol / total_ce_vol if total_ce_vol > 0 else 0

        return {
            "pcr_oi": round(pcr_oi, 2),
            "pcr_volume": round(pcr_vol, 2),
            "total_ce_oi": int(total_ce_oi),
            "total_pe_oi": int(total_pe_oi)
        }

    def find_walls(self, option_chain: pd.DataFrame) -> Dict[str, float]:
        """
        Identify Call Wall (Resistance) and Put Wall (Support).
        Strike with highest OI for CE is Call Wall.
        Strike with highest OI for PE is Put Wall.
        """
        ce_chain = option_chain[option_chain['option_type'] == 'CE']
        pe_chain = option_chain[option_chain['option_type'] == 'PE']

        call_wall = ce_chain.loc[ce_chain['oi'].idxmax()]['strike'] if not ce_chain.empty else 0
        put_wall = pe_chain.loc[pe_chain['oi'].idxmax()]['strike'] if not pe_chain.empty else 0

        return {
            "call_wall": call_wall,
            "put_wall": put_wall
        }

    def calculate_max_pain(self, option_chain: pd.DataFrame) -> float:
        """
        Calculate Max Pain strike (strike where option writers lose the least).
        """
        strikes = option_chain['strike'].unique()
        pain = {}

        for price in strikes:
            total_loss = 0

            # CE writers lose if Price > Strike
            ce_loss = option_chain[
                (option_chain['option_type'] == 'CE') & (option_chain['strike'] < price)
            ].apply(lambda x: (price - x['strike']) * x['oi'], axis=1).sum()

            # PE writers lose if Price < Strike
            pe_loss = option_chain[
                (option_chain['option_type'] == 'PE') & (option_chain['strike'] > price)
            ].apply(lambda x: (x['strike'] - price) * x['oi'], axis=1).sum()

            pain[price] = ce_loss + pe_loss

        # Return strike with minimum pain
        return min(pain, key=pain.get) if pain else 0.0

oi_analyzer = OIAnalyzer()
