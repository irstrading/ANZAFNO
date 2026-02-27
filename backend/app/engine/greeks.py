import numpy as np
import pandas as pd
from py_vollib_vectorized import vectorized_implied_volatility, get_all_greeks
from datetime import datetime

class GreeksEngine:
    """
    High-performance Greeks calculator using py_vollib_vectorized.
    Computes Delta, Gamma, Vega, Theta, Rho for entire option chain at once.
    """

    def calculate_greeks(
        self,
        df: pd.DataFrame,
        spot_price: float,
        risk_free_rate: float = 0.065  # India 10Y G-Sec yield approx
    ) -> pd.DataFrame:
        """
        Input DataFrame must have columns:
        ['strike', 'expiry', 'option_type' (c/p), 'ltp', 'volume', 'oi']

        Returns DataFrame with added columns:
        ['iv', 'delta', 'gamma', 'vega', 'theta', 'rho']
        """

        # Calculate time to expiry in years
        current_time = datetime.now()
        df['time_to_expiry'] = (pd.to_datetime(df['expiry']) - current_time).dt.total_seconds() / (365 * 24 * 3600)

        # Filter out expired options or zero time
        df = df[df['time_to_expiry'] > 0].copy()

        # Calculate Implied Volatility
        # vectorized_implied_volatility(price, S, K, t, r, flag, q)
        # q=0 for no dividends (simplified)

        # Prepare inputs
        S = spot_price
        K = df['strike'].values
        t = df['time_to_expiry'].values
        r = risk_free_rate
        flag = df['option_type'].values # 'c' or 'p'
        price = df['ltp'].values

        # 1. Calculate IV
        try:
            iv = vectorized_implied_volatility(price, S, K, t, r, flag, q=0, return_as='numpy')
            df['iv'] = iv
        except Exception as e:
            # Fallback or handle calculation errors (e.g., deep OTM/ITM can fail)
            df['iv'] = 0.0

        # Handle NaN IVs (replace with 0 or exclude)
        df['iv'] = df['iv'].fillna(0)

        # 2. Calculate Greeks using the computed IV
        # get_all_greeks(flag, S, K, t, r, sigma, q, model='black_scholes')
        sigma = df['iv'].values

        try:
            greeks = get_all_greeks(flag, S, K, t, r, sigma, q=0, model='black_scholes', return_as='dataframe')

            # Merge greeks back to original DF
            df['delta'] = greeks['delta']
            df['gamma'] = greeks['gamma']
            df['theta'] = greeks['theta']
            df['vega'] = greeks['vega']
            df['rho'] = greeks['rho']

        except Exception as e:
            # Fallback
            df['delta'] = 0.0
            df['gamma'] = 0.0
            df['theta'] = 0.0
            df['vega'] = 0.0
            df['rho'] = 0.0

        return df

    def calculate_vanna_charm(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate second-order greeks: Vanna (dDelta/dVol) and Charm (dDelta/dTime)
        Useful for dealer positioning analysis.
        """
        # Placeholder: py_vollib_vectorized doesn't output Vanna/Charm directly
        # Would implement manual Black-Scholes formulas here if needed for advanced analysis

        # Vanna = -e(-qt) * N'(d1) * d2 / sigma
        # Charm = -e(-qt) * [N'(d1) * (2(r-q)t - d2*sigma*sqrt(t)) / (2t*sigma*sqrt(t))] ... simplified

        return df

greeks_engine = GreeksEngine()
