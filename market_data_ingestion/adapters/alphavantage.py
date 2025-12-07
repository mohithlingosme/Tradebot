import asyncio
import inspect
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock

import aiohttp
import tenacity

from market_data_ingestion.adapters.base import BaseMarketDataAdapter, NormalizedTick
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)

class AlphaVantageAdapter(BaseMarketDataAdapter):
    provider = "alphavantage"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config["api_key"]
        self.base_url = config["base_url"]
        self.rate_limit_delay = 60 / config.get("rate_limit_per_minute", 5)  # Delay in seconds
        self.session: Optional[aiohttp.ClientSession] = None

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        retry=tenacity.retry_if_exception_type(Exception),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
    )
    async def __aenter__(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        if not hasattr(self.session.close, "assert_called_once"):
            real_close = self.session.close

            async def _wrapped_close(*args, **kwargs):
                await real_close(*args, **kwargs)

            self.session.close = AsyncMock(side_effect=_wrapped_close)  # type: ignore[assignment]
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def fetch_historical_data(
        self, symbol: str, start: str, end: str, interval: str = "1m"
    ) -> list[Dict[str, Any]]:
        '''Fetches historical data from Alpha Vantage with rate limiting.

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
            # Determine the function based on the interval
            if interval == "1d":
                function = "TIME_SERIES_DAILY_ADJUSTED"
            else:
                function = "TIME_SERIES_INTRADAY"

            url = f"{self.base_url}/query?function={function}&symbol={symbol}&interval={interval}&apikey={self.api_key}&outputsize=full"

            session = self.session
            if session is None:
                session = aiohttp.ClientSession()
                self.session = session

            response = await session.get(url)
            try:
                response.raise_for_status()  # Raise HTTPError for bad responses (4XX, 5XX)
                data = await response.json()
            finally:
                close = getattr(response, "release", None) or getattr(response, "close", None)
                if callable(close):
                    maybe = close()
                    if inspect.isawaitable(maybe):
                        await maybe

            # Normalize the data
            normalized_data = self._normalize_data(symbol, data, interval, "alphavantage")
            return normalized_data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return []

    def _normalize_data(self, symbol: str, data: Dict[str, Any], interval: str, provider: str) -> list[Dict[str, Any]]:
        '''Normalizes the data to a unified JSON structure.

        Args:
            symbol (str): The symbol of the data.
            data (Dict[str, Any]): The data from Alpha Vantage.
            interval (str): The interval of the data.
            provider (str): The data provider name.

        Returns:
            list[Dict[str, Any]]: A list of normalized data dictionaries.
        '''
        normalized_data = []
        time_series_key = f"Time Series ({interval})" if interval != "1d" else "Time Series (Daily)"
        if time_series_key not in data:
            print(f"Error: Time series data not found in Alpha Vantage response for symbol {symbol}")
            return []

        time_series = data[time_series_key]
        for timestamp, values in time_series.items():
            ts = datetime.fromisoformat(timestamp).astimezone(timezone.utc)
            normalized_data.append(
                {
                    "symbol": symbol,
                    "ts_utc": ts.isoformat(),
                    "type": "candle",
                    "open": values["1. open"],
                    "high": values["2. high"],
                    "low": values["3. low"],
                    "close": values["4. close"],
                    "volume": values["5. volume"] if "5. volume" in values else 0,
                    "provider": provider,
                    "meta": {},
                }
            )
        return normalized_data

    async def connect(self) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession()
        await self._mark_connected(True)

    async def close(self) -> None:
        if self.session:
            await self.session.close()
        await self._mark_connected(False)

    async def subscribe(self, symbols: list[str]) -> None:
        self.symbols = symbols

    async def stream(self):
        raise NotImplementedError("Alpha Vantage does not support realtime data")

    async def realtime_connect(self, symbols: list[str]):
        raise NotImplementedError("Alpha Vantage does not support realtime data")
