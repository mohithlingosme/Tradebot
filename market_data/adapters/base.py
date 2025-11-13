"""
Base provider adapter interface.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime


class ProviderAdapter(ABC):
    """Abstract base class for market data provider adapters."""

    def __init__(self, config: Dict):
        self.config = config

    @abstractmethod
    async def stream_trades(self, symbol: str) -> AsyncGenerator[Dict, None]:
        """
        Stream real-time trades for a symbol.

        Args:
            symbol: Trading symbol

        Yields:
            Trade data dictionaries in provider-specific format
        """
        pass

    @abstractmethod
    async def fetch_trades(self, symbol: str, start_time: datetime,
                          end_time: datetime) -> List[Dict]:
        """
        Fetch historical trades for a symbol.

        Args:
            symbol: Trading symbol
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of trade data dictionaries
        """
        pass

    @abstractmethod
    async def stream_quotes(self, symbol: str) -> AsyncGenerator[Dict, None]:
        """
        Stream real-time quotes for a symbol.

        Args:
            symbol: Trading symbol

        Yields:
            Quote data dictionaries in provider-specific format
        """
        pass

    @abstractmethod
    async def fetch_candles(self, symbol: str, interval: str,
                           start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Fetch historical candles for a symbol.

        Args:
            symbol: Trading symbol
            interval: Candle interval (e.g., '1m', '5m', '1h')
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of candle data dictionaries
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass
