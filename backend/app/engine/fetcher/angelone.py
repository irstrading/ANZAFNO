import time
import logging
from typing import Dict, Any, List
from datetime import datetime
from SmartApi import SmartConnect
from app.core.config import settings
from .base import DataFetcher

logger = logging.getLogger(__name__)

class AngelOneFetcher(DataFetcher):
    def __init__(self):
        self.api_key = settings.ANGEL_API_KEY
        self.client_id = settings.ANGEL_CLIENT_ID
        self.password = settings.ANGEL_PASSWORD
        self.totp_key = settings.ANGEL_TOTP_KEY
        self.smart_api = None
        self.session = None

    def connect(self) -> bool:
        try:
            if not self.api_key:
                logger.warning("AngelOne API Key not found in settings")
                return False

            self.smart_api = SmartConnect(api_key=self.api_key)
            import pyotp
            totp = pyotp.TOTP(self.totp_key).now()

            data = self.smart_api.generateSession(self.client_id, self.password, totp)

            if data['status']:
                self.session = data['data']
                logger.info(f"Connected to AngelOne: {self.client_id}")
                return True
            else:
                logger.error(f"AngelOne Login Failed: {data['message']}")
                return False

        except Exception as e:
            logger.error(f"AngelOne Connection Error: {e}")
            return False

    def get_quote(self, symbol: str, token: str, exchange: str = "NSE") -> Dict[str, Any]:
        if not self.smart_api:
            self.connect()

        try:
            # AngelOne logic for LTP
            # Note: LTP API requires a list, but we wrap it for single
            response = self.smart_api.ltpData(exchange, symbol, token)
            if response['status']:
                return response['data']
            return {}
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return {}

    def get_option_chain(self, symbol: str, expiry: datetime) -> List[Dict[str, Any]]:
        # AngelOne implementation for option chain logic
        # Typically involves fetching multiple tokens or using a dedicated endpoint if available
        # Placeholder for implementation
        return []

    def get_historical_data(self, token: str, interval: str, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        if not self.smart_api:
            self.connect()

        try:
            params = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
                "todate": to_date.strftime("%Y-%m-%d %H:%M")
            }
            response = self.smart_api.getCandleData(params)
            if response['status']:
                return response['data']
            return []
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []
