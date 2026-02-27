# backend/app/core/gex.py

import pandas as pd
from typing import Dict, List, Any

class DealerExposureEngine:
    """
    Assumes market makers are counterparty to all trades.
    Dealers BUY calls when retail SELLS, and SELL puts when retail BUYS.
    Hedge direction is opposite of their book.
    """

    def calculate_exposures(self, option_chain: List[Dict], spot: float) -> Dict[str, float]:
        gex = 0.0
        dex = 0.0
        vex = 0.0
        cex = 0.0

        for row in option_chain:
            # LOT SIZE is needed. Assuming it's in the row or passed.
            # If not in row, we need to pass it or look it up.
            # For this strict implementation, let's assume 'lot_size' is in row.
            lot_size = row.get('lot_size', 50) # Default or fetch

            # Call side
            call_oi = row.get('call_oi', 0)
            call_gamma = row.get('ce_gamma', 0)
            call_delta = row.get('ce_delta', 0)
            call_vanna = row.get('ce_vanna', 0)
            call_charm = row.get('ce_charm', 0)
            call_iv = row.get('ce_iv', 0)

            # Put side
            put_oi = row.get('put_oi', 0)
            put_gamma = row.get('pe_gamma', 0)
            put_delta = row.get('pe_delta', 0)
            put_vanna = row.get('pe_vanna', 0)
            put_charm = row.get('pe_charm', 0)
            put_iv = row.get('pe_iv', 0)

            # GEX = Gamma * OI * spot^2 * 0.01
            # Calls: Dealers are short calls -> negative gamma exposure
            # Puts: Dealers are short puts -> positive gamma exposure (long the market, short volatility)
            # Actually, standard GEX theory:
            # Dealer sells Call -> Short Call -> Short Gamma.
            # Dealer sells Put -> Short Put -> Long Gamma (because they want market to go up/stay flat).

            # Correct sign convention per SpotGamma/ANZA docs:
            # Call GEX contribution: -1 * Gamma * OI
            # Put GEX contribution: +1 * Gamma * OI

            gex += (-1 * call_gamma * call_oi * lot_size * (spot**2) * 0.01)
            gex += (1 * put_gamma * put_oi * lot_size * (spot**2) * 0.01)

            # DEX = Delta * OI * lot_size
            # Call DEX (Dealer Short Call): Dealer has negative delta. To hedge, they buy.
            # Put DEX (Dealer Short Put): Dealer has positive delta. To hedge, they sell.
            # Wait, let's stick to the "Directional pressure dealers must hedge"
            # If Dealer is Short Call (Delta ~ 0.5), their position delta is -0.5. They are Short.
            # To hedge, they must be Long underlying.
            # Net Delta Exposure (DEX) represents the Dealer's book delta.
            # If DEX is positive, Dealers are Long -> They sell to hedge?
            # Usually DEX is framed as "Amount of underlying dealers must buy/sell per 1% move"
            # Let's use standard:
            # Dealer Call Delta = -1 * Call Delta
            # Dealer Put Delta = -1 * Put Delta (Put delta is negative, so this becomes positive)

            dex += (-1 * call_delta) * call_oi * lot_size
            dex += (-1 * put_delta) * put_oi * lot_size

            # VEX = Vanna * OI * lot_size * spot * IV
            # Vanna = dDelta/dSigma.
            # If IV rises, how does Delta change?
            # Dealers adjust hedges based on this.
            vex += (-1 * call_vanna) * call_oi * lot_size * spot * call_iv
            vex += (-1 * put_vanna) * put_oi * lot_size * spot * put_iv

            # CEX = Charm * OI * lot_size
            # Charm = dDelta/dTime
            cex += (-1 * call_charm) * call_oi * lot_size
            cex += (-1 * put_charm) * put_oi * lot_size

        return {
            'gex': gex,
            'dex': dex,
            'vex': vex,
            'cex': cex
        }

    def gex_flip_level(self, option_chain: List[Dict], spot: float) -> float:
        """
        Approximation of strike where cumulative GEX crosses zero.
        """
        # Sort by strike
        sorted_chain = sorted(option_chain, key=lambda x: x['strike'])

        cumulative_gex = 0
        flip_strike = 0

        gex_profile = []

        for row in sorted_chain:
            lot_size = row.get('lot_size', 50)
            strike = row['strike']

            call_gex = -1 * row.get('ce_gamma', 0) * row.get('call_oi', 0) * lot_size * (spot**2) * 0.01
            put_gex = 1 * row.get('pe_gamma', 0) * row.get('put_oi', 0) * lot_size * (spot**2) * 0.01

            net_gex = call_gex + put_gex
            cumulative_gex += net_gex
            gex_profile.append((strike, cumulative_gex))

        # Find zero crossing
        for i in range(1, len(gex_profile)):
            prev_strike, prev_val = gex_profile[i-1]
            curr_strike, curr_val = gex_profile[i]

            if prev_val > 0 and curr_val < 0:
                return (prev_strike + curr_strike) / 2
            if prev_val < 0 and curr_val > 0:
                return (prev_strike + curr_strike) / 2

        return 0.0
