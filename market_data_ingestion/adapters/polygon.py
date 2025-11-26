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


class PolygonAdapter(BaseMarketDataAdapter):
    provider = "polygon"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.polygon.io")
        self.rate_limit_delay = 60 / config.get("rate_limit_per_minute", 300)
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
        raise NotImplementedError("Polygon websocket streaming not implemented")

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(Exception),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
    )
    async def fetch_aggregates(
        self, symbol: str, start: str, end: str, timespan: str = "minute", limit: int = 5000
    ) -> List[Dict[str, Any]]:
        await asyncio.sleep(self.rate_limit_delay)
        if not self.session:
            self.session = aiohttp.ClientSession()
        url = (
            f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/{timespan}/{start}/{end}"
            f"?adjusted=true&sort=asc&limit={limit}&apiKey={self.api_key}"
        )
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            payload = await resp.json()
        results = payload.get("results", [])
        return [self._normalize_aggregate(symbol, r) for r in results]

    def _normalize_aggregate(self, symbol: str, row: Dict[str, Any]) -> Dict[str, Any]:
        ts = datetime.fromtimestamp(row["t"] / 1000, tz=timezone.utc)
        return {
            "symbol": symbol,
            "ts_utc": ts.isoformat(),
            "type": "candle",
            "open": float(row.get("o", 0)),
            "high": float(row.get("h", 0)),
            "low": float(row.get("l", 0)),
            "close": float(row.get("c", 0)),
            "volume": float(row.get("v", 0)),
            "provider": self.provider,
            "meta": {},
        }
