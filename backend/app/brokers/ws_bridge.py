# backend/app/brokers/ws_bridge.py
import os
import json
import logging
import asyncio
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from app.brokers.angelone import AngelOneAdapter
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

async def run_ws_bridge():
    api_key = os.getenv("ANGEL_API_KEY")
    client_id = os.getenv("ANGEL_CLIENT_ID")
    password = os.getenv("ANGEL_PASSWORD")
    totp_secret = os.getenv("ANGEL_TOTP_SECRET")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

    adapter = AngelOneAdapter(api_key, client_id, password, totp_secret)
    session_data = adapter.login()

    redis = await aioredis.from_url(redis_url)

    sws = SmartWebSocketV2(session_data['jwtToken'], api_key, client_id, session_data['feedToken'])

    def on_data(wsapp, msg):
        logger.info(f"Ticks: {msg}")
        # Publish to Redis for internal consumers
        asyncio.run(redis.publish("anza:market_data", json.dumps(msg)))

    def on_open(wsapp):
        logger.info("on open")
        # Example subscription: Nifty and BankNifty Futures
        correlation_id = "anza_ws_01"
        action = 1 # Subscribe
        mode = 3 # Full
        token_list = [
            {"exchangeType": 1, "tokens": ["26000", "26009"]} # Placeholder tokens
        ]
        sws.subscribe(correlation_id, mode, token_list)

    def on_error(wsapp, error):
        logger.error(f"WS Error: {error}")

    def on_close(wsapp):
        logger.info("on close")

    sws.on_open = on_open
    sws.on_data = on_data
    sws.on_error = on_error
    sws.on_close = on_close

    sws.connect()

if __name__ == "__main__":
    asyncio.run(run_ws_bridge())
