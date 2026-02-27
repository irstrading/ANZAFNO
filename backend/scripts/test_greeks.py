from app.engine.greeks import greeks_engine
import pandas as pd
from datetime import datetime, timedelta

def test_greeks():
    # Mock Option Chain Data
    data = {
        'strike': [21500, 21600, 21700, 21500, 21600, 21700],
        'expiry': [(datetime.now() + timedelta(days=5)).isoformat()] * 6,
        'option_type': ['c', 'c', 'c', 'p', 'p', 'p'],
        'ltp': [200, 150, 100, 50, 80, 120],
        'volume': [1000, 5000, 2000, 800, 1200, 3000],
        'oi': [10000, 50000, 20000, 8000, 12000, 30000]
    }

    df = pd.DataFrame(data)
    spot_price = 21600

    print("Input Data:")
    print(df)

    result = greeks_engine.calculate_greeks(df, spot_price)

    print("\nCalculated Greeks:")
    print(result[['strike', 'option_type', 'ltp', 'iv', 'delta', 'gamma', 'vega', 'theta']])

if __name__ == "__main__":
    test_greeks()
