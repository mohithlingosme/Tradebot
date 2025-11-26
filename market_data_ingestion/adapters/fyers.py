from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import tenacity

from market_data_ingestion.adapters.base import BaseMarketDataAdapter, NormalizedTick
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)


class FyersAdapter(BaseMarketDataAdapter):
    provider = "fyers"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.access_token = config.get("access_token")
        self.base_url = config.get("base_url", "https://api-t1.fyers.in/data")
        self.rate_limit_delay = 60 / config.get("rate_limit_per_minute", 60)
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> None:
        self.session = aiohttp.ClientSession()
        await self._mark_connected(True)

    async def close(self) -> None:
        if self.session:
            await self.session.close()
        await self._mark_connected(False)

    async def subscribe(self, symbols: List[str]) -> None:
        self.symbols = symbols

    async def stream(self):
        """Fyers provides polling APIs; realtime streaming is not implemented here."""
        raise NotImplementedError("Fyers streaming not implemented in this minimal adapter")

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=15),
        retry=tenacity.retry_if_exception_type(Exception),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
    )
    async def fetch_historical_data(
        self, symbol: str, start: str, end: str, interval: str = "1"
    ) -> List[Dict[str, Any]]:
        await asyncio.sleep(self.rate_limit_delay)
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        url = f"{self.base_url}/history/?symbol={symbol}&resolution={interval}&date_format=1&range_from={start}&range_to={end}"
        if not self.session:
            self.session = aiohttp.ClientSession()
        async with self.session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            payload = await resp.json()
        candles = payload.get("candles", [])
        return [self._normalize_candle(symbol, c) for c in candles]

    def _normalize_candle(self, symbol: str, candle: List[Any]) -> Dict[str, Any]:
        # Fyers returns [epoch, open, high, low, close, volume]
        ts = datetime.fromtimestamp(candle[0], tz=timezone.utc)
        return {
            "symbol": symbol,
            "ts_utc": ts.isoformat(),
            "type": "candle",
            "open": float(candle[1]),
            "high": float(candle[2]),
            "low": float(candle[3]),
            "close": float(candle[4]),
            "volume": float(candle[5]),
            "provider": self.provider,
            "meta": {},
        }
