# backend/app/core/oi_analysis.py
import pandas as pd
class OIAnalysisEngine:
    def detect_signal(self, price_change, futures_oi_change):
        if price_change > 0.05 and futures_oi_change > 100: return "LONG_BUILDUP"
        if price_change < -0.05 and futures_oi_change > 100: return "SHORT_BUILDUP"
        if price_change > 0.05 and futures_oi_change < -100: return "SHORT_COVERING"
        if price_change < -0.05 and futures_oi_change < -100: return "LONG_UNWINDING"
        return "NEUTRAL"
    def find_walls(self, df):
        if df.empty: return {"call_wall": 0, "put_wall": 0}
        call_wall = df[df['option_type'] == 'CE'].loc[df[df['option_type'] == 'CE']['oi'].idxmax()]['strike'] if not df[df['option_type'] == 'CE'].empty else 0
        put_wall = df[df['option_type'] == 'PE'].loc[df[df['option_type'] == 'PE']['oi'].idxmax()]['strike'] if not df[df['option_type'] == 'PE'].empty else 0
        return {"call_wall": call_wall, "put_wall": put_wall}
