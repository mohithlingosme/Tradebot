import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd
import tenacity
import yfinance as yf

from market_data_ingestion.adapters.base import BaseMarketDataAdapter, NormalizedTick
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)

class YFinanceAdapter(BaseMarketDataAdapter):
    provider = "yfinance"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limit_delay = 60 / config.get("rate_limit_per_minute", 100)  # Delay in seconds

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type(Exception),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
    )
    async def fetch_historical_data(
        self, symbol: str, start: str, end: str, interval: str = "1m"
    ) -> list[Dict[str, Any]]:
        '''Fetches historical data from yfinance with rate limiting.

        Args:
            symbol (str): The symbol to fetch data for (e.g., "RELIANCE.NS").
            start (str): The start date in "YYYY-MM-DD" format.
            end (str): The end date in "YYYY-MM-DD" format.
            interval (str): The interval (e.g., "1m", "5m", "1d").

        Returns:
            list[Dict[str, Any]]: A list of normalized data dictionaries.
        '''
        # Rate limiting: wait before making request
        await asyncio.sleep(self.rate_limit_delay)

        try:
            # Download data from yfinance
            data = yf.download(symbol, start=start, end=end, interval=interval)

            # Normalize the data
            normalized_data = self._normalize_data(symbol, data, interval, "yfinance")
            return normalized_data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return []

    def _normalize_data(self, symbol: str, data: pd.DataFrame, interval: str, provider: str) -> list[Dict[str, Any]]:
        '''Normalizes the data to a unified JSON structure.

        Args:
            symbol (str): The symbol of the data.
            data (pd.DataFrame): The data from yfinance.
            interval (str): The interval of the data.
            provider (str): The data provider name.

        Returns:
            list[Dict[str, Any]]: A list of normalized data dictionaries.
        '''
        normalized_data = []
        for index, row in data.iterrows():
            normalized_data.append(
                {
                    "symbol": symbol,
                    "ts_utc": str(index.to_pydatetime().astimezone(timezone.utc)),
                    "type": "candle",
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                    "provider": provider,
                    "meta": {},
                }
            )
        return normalized_data

    async def connect(self) -> None:
        await self._mark_connected(True)

    async def close(self) -> None:
        await self._mark_connected(False)

    async def subscribe(self, symbols: list[str]) -> None:
        # yfinance is pull-only; nothing to do for subscribe
        self.symbols = symbols

    async def stream(self):
        raise NotImplementedError("yfinance does not support realtime data")
