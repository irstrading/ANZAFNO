import logging
from typing import Dict, Any, List
from .base import DataFetcher
from .angelone import AngelOneFetcher
from .openalgo import OpenAlgoFetcher
from app.core.config import settings

logger = logging.getLogger(__name__)

class MarketDataManager:
    def __init__(self):
        self.fetcher: DataFetcher = self._get_fetcher()
        self.connected = False

    def _get_fetcher(self) -> DataFetcher:
        if settings.OPENALGO_HOST:
            logger.info("Using OpenAlgo Fetcher")
            return OpenAlgoFetcher()
        else:
            logger.info("Using AngelOne Fetcher")
            return AngelOneFetcher()

    async def initialize(self):
        if not self.connected:
            self.connected = self.fetcher.connect()

    async def fetch_indices(self) -> Dict[str, float]:
        """Fetch NIFTY and BANKNIFTY Spot prices"""
        if not self.connected:
            await self.initialize()

        # Example tokens for AngelOne (Indices)
        # NIFTY 50: 99926000, BANKNIFTY: 99926009 (NSE)
        # Need to map these correctly based on fetcher implementation
        return {}

    async def fetch_option_chain(self, symbol: str) -> List[Dict[str, Any]]:
        if not self.connected:
            await self.initialize()

        # Logic to fetch raw option chain data
        # This will be passed to Greeks Engine
        return []
