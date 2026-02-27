import pandas as pd
from app.core.black76 import Black76Engine
from app.core.dealer_exposure import DealerExposureEngine
from app.core.oi_analysis import OIAnalysisEngine

def test_greeks():
    engine = Black76Engine()
    res = engine.price_and_greeks(23500, 23500, 7/365, 0.15, 'CE')
    print(f"Price: {res.price}, Delta: {res.delta}, Gamma: {res.gamma}")
    assert res.delta > 0
    assert res.gamma > 0

def test_gex():
    de_engine = DealerExposureEngine()
    df = pd.DataFrame([
        {'option_type': 'CE', 'gamma': 0.001, 'oi': 10000, 'lot_size': 50, 'strike': 23500},
        {'option_type': 'PE', 'gamma': 0.001, 'oi': 10000, 'lot_size': 50, 'strike': 23500}
    ])
    gex = de_engine.compute_gex(df, 23500)
    print(f"GEX: {gex}")
    assert abs(gex) < 1e-5

if __name__ == "__main__":
    test_greeks()
    test_gex()
    print("Core tests passed!")
