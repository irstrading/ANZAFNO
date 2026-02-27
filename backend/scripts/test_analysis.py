from app.engine.analysis import oi_analyzer, Sentiment
import pandas as pd

def test_analysis():
    # Mock Data
    data = {
        'strike': [21500, 21600, 21700, 21500, 21600, 21700],
        'option_type': ['CE', 'CE', 'CE', 'PE', 'PE', 'PE'],
        'oi': [10000, 50000, 20000, 8000, 12000, 30000], # High PE OI at 21700 (Put Wall?), High CE OI at 21600 (Call Wall?)
        'volume': [1000, 5000, 2000, 800, 1200, 3000]
    }
    df = pd.DataFrame(data)

    print("Option Chain Data:")
    print(df)

    # 1. Test PCR
    pcr_result = oi_analyzer.calculate_pcr(df)
    print("\nPCR Analysis:")
    print(pcr_result)

    # 2. Test Walls
    walls = oi_analyzer.find_walls(df)
    print("\nSupport & Resistance:")
    print(f"Call Wall (Res): {walls['call_wall']}")
    print(f"Put Wall (Sup): {walls['put_wall']}")

    # 3. Test Max Pain
    max_pain = oi_analyzer.calculate_max_pain(df)
    print(f"\nMax Pain Strike: {max_pain}")

    # 4. Test Buildup
    sentiment = oi_analyzer.analyze_buildup(ltp_change=5.0, oi_change=1000)
    print(f"\nBuildup Analysis (LTP +5, OI +1000): {sentiment.value}")

if __name__ == "__main__":
    test_analysis()
