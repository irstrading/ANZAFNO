from app.celery_app import celery_app
from app.engine.manager import MarketDataManager
from app.engine.greeks import greeks_engine
from app.engine.analysis import oi_analyzer
from app.db.session import SessionLocal
from app.models.market import OptionChain, AnalysisResult
from datetime import datetime
import pandas as pd
import asyncio

manager = MarketDataManager()

@celery_app.task
def fetch_market_data_task():
    """
    Periodic task to fetch live market data (LTP, OHLC) and update cache/DB.
    """
    # Run async function in sync Celery task
    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager.fetch_indices())

@celery_app.task
def process_option_chain_task(symbol: str):
    """
    Fetch Option Chain -> Calculate Greeks -> Analyze OI -> Store in DB.
    """
    db = SessionLocal()
    try:
        # 1. Fetch Raw Data
        loop = asyncio.get_event_loop()
        raw_chain = loop.run_until_complete(manager.fetch_option_chain(symbol))

        if not raw_chain:
            return "No Data"

        # Convert to DataFrame
        df = pd.DataFrame(raw_chain)

        # 2. Calculate Greeks
        # Need spot price first (fetch from DB or Manager)
        spot_price = 21500 # Placeholder, fetch real spot
        df_greeks = greeks_engine.calculate_greeks(df, spot_price)

        # 3. Analyze OI
        pcr = oi_analyzer.calculate_pcr(df_greeks)
        walls = oi_analyzer.find_walls(df_greeks)
        max_pain = oi_analyzer.calculate_max_pain(df_greeks)

        # 4. Store Analysis Result
        analysis = AnalysisResult(
            time=datetime.now(),
            symbol=symbol,
            expiry=df['expiry'].iloc[0], # Assuming single expiry batch
            pcr=pcr['pcr_oi'],
            pcr_change=0.0, # Need previous value to calc change
            max_pain=max_pain,
            call_wall=walls['call_wall'],
            put_wall=walls['put_wall']
        )
        db.add(analysis)

        # 5. Store Option Chain (Batch Insert)
        # Convert DF rows to OptionChain model instances...

        db.commit()
        return f"Processed {symbol}"

    except Exception as e:
        db.rollback()
        return f"Error: {str(e)}"
    finally:
        db.close()
