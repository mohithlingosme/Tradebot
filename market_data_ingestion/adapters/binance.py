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


class BinanceAdapter(BaseMarketDataAdapter):
    provider = "binance"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "https://api.binance.com/api/v3")
        self.rate_limit_delay = 60 / config.get("rate_limit_per_minute", 1200)
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
        """Streaming via websockets is out of scope here."""
        raise NotImplementedError("Binance websocket streaming not implemented")

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        retry=tenacity.retry_if_exception_type(Exception),
        before_sleep=tenacity.before_sleep_log(logger, logging.WARNING),
    )
    async def fetch_klines(self, symbol: str, interval: str = "1m", limit: int = 500) -> List[Dict[str, Any]]:
        await asyncio.sleep(self.rate_limit_delay)
        if not self.session:
            self.session = aiohttp.ClientSession()
        url = f"{self.base_url}/klines?symbol={symbol}&interval={interval}&limit={limit}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return [self._normalize_kline(symbol, k) for k in data]

    def _normalize_kline(self, symbol: str, kline: List[Any]) -> Dict[str, Any]:
        ts = datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc)
        return {
            "symbol": symbol,
            "ts_utc": ts.isoformat(),
            "type": "candle",
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5]),
            "provider": self.provider,
            "meta": {},
        }
