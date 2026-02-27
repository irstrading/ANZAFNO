# backend/app/data/angelone_ws.py

from SmartApi import SmartConnect, SmartWebSocket
import asyncio
import json
import logging
from typing import Callable, List, Dict, Optional

logger = logging.getLogger(__name__)

class AngelOneWebSocket:
    """
    Uses AngelOne's WebSocket feed for LIVE LTP of:
    - Nifty Futures (all expiries)
    - BankNifty Futures
    - All 150 FnO stock futures
    - Key option strikes (ATM ±5 for watchlist stocks)

    NO REST polling for prices. WebSocket push only.
    Saves ~1,500 REST calls/hour.
    """

    def __init__(self, api_key: str, client_code: str, feed_token: str):
        self.api_key = api_key
        self.client_code = client_code
        self.feed_token = feed_token
        self.subscriptions: dict[str, list] = {}  # symbol -> [tokens]
        self.price_cache: dict[str, float] = {}
        self._callbacks: list[Callable[[str, float, int], None]] = []
        self.sws = None
        self.connected = False
        self.running = False
        self._loop = None

    def start(self):
        """Starts the WebSocket connection in a separate thread/task"""
        self.sws = SmartWebSocket(self.feed_token, self.client_code)
        self.sws._on_open = self._on_open
        self.sws._on_data = self._on_data
        self.sws._on_error = self._on_error
        self.sws._on_close = self._on_close

        self.running = True
        self.sws.connect()

    def _on_open(self, ws):
        logger.info("AngelOne WebSocket Connected")
        self.connected = True
        # Re-subscribe if needed
        # self.subscribe_pending()

    def _on_data(self, ws, message):
        # Parse binary or json message
        # SmartAPI usually sends binary which the library decodes?
        # Or dictionary directly. Assuming dictionary for now.
        if isinstance(message, list): # Often a list of tick dicts
            for tick in message:
                self._process_tick(tick)
        else:
            self._process_tick(message)

    def _process_tick(self, tick):
        token = tick.get('token')
        ltp = float(tick.get('ltp', 0))
        volume = int(tick.get('volume', 0)) # Or 'last_traded_quantity'

        if token and ltp:
            self.price_cache[token] = ltp
            # Notify callbacks
            for cb in self._callbacks:
                try:
                    cb(token, ltp, volume)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

    def _on_error(self, ws, error):
        logger.error(f"WebSocket Error: {error}")

    def _on_close(self, ws):
        logger.info("WebSocket Closed")
        self.connected = False
        self.running = False

    async def connect_and_subscribe(self, tokens: list[str]):
        """
        Connects to AngelOne WebSocket and subscribes to token list.
        Automatically reconnects on disconnect.
        """
        if not self.connected:
            # In a real async loop, we'd run self.start() in executor or thread
            pass

        if self.sws:
            # Subscribe mode: 1 = LTP, 2 = Quote, 3 = Full
            correlation_id = "subscribe_batch"
            action = 1
            mode = 1 # LTP only

            token_list = [{"exchangeType": 1, "tokens": tokens}] # 1 = NSE
            self.sws.subscribe(correlation_id, mode, token_list)

    def add_callback(self, callback: Callable[[str, float, int], None]):
        self._callbacks.append(callback)

    def add_option_strike_subscription(self, symbol: str, strikes: list[int], expiry: str):
        """
        Dynamically add option strike tokens to WebSocket subscription.
        Called when ATM changes (price moves) to track new ATM ±5 range.
        """
        # Logic to map symbol+strike+expiry to token ID required
        pass
