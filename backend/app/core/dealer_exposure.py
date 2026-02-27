# backend/app/core/dealer_exposure.py
import pandas as pd
class DealerExposureEngine:
    def compute_gex(self, df: pd.DataFrame, spot: float) -> float:
        if df.empty: return 0.0
        df = df.copy()
        df['sign'] = df['option_type'].map({'CE': -1, 'PE': 1})
        df['gex_val'] = df['sign'] * df['gamma'] * df['oi'] * df['lot_size'] * (spot**2) * 0.01
        return float(df['gex_val'].sum())
