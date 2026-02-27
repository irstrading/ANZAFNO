from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime

class DataFetcher(ABC):
    """
    Abstract base class for data fetchers.
    All broker implementations must inherit from this.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Authenticate and establish connection"""
        pass

    @abstractmethod
    def get_quote(self, symbol: str, token: str) -> Dict[str, Any]:
        """Fetch real-time quote (LTP, OHLC, Volume)"""
        pass

    @abstractmethod
    def get_option_chain(self, symbol: str, expiry: datetime) -> List[Dict[str, Any]]:
        """Fetch full option chain for a symbol and expiry"""
        pass

    @abstractmethod
    def get_historical_data(self, token: str, interval: str, from_date: datetime, to_date: datetime) -> List[Dict[str, Any]]:
        """Fetch historical candles"""
        pass
