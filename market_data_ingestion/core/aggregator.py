from __future__ import annotations

"""
Realtime tick-to-candle aggregation utilities.

This module ingests normalized ticks from any adapter and produces OHLCV
candles for multiple intervals (1s/5s/1m by default). It is intentionally
stateless outside the in-memory buffers so it can backpressure-friendly
pipelines (async queues, websocket streams, etc.).
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Iterable, MutableMapping, Optional, Tuple

from market_data_ingestion.adapters.base import NormalizedTick
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)

CandlePayload = Dict[str, object]
OnCandleCallback = Callable[[CandlePayload], Awaitable[None] | None]


@dataclass
class _CandleBuffer:
    """Mutable OHLCV accumulator for a symbol/interval bucket."""

    symbol: str
    interval_seconds: int
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    last_tick_at: Optional[datetime] = None

    def update(self, price: float, volume: float, ts: datetime) -> None:
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.volume += volume
        self.last_tick_at = ts

    def to_payload(self) -> CandlePayload:
        return {
            "symbol": self.symbol,
            "timestamp": self.open_time,
            "interval": f"{self.interval_seconds}s",
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "last_tick_at": self.last_tick_at or self.open_time,
        }


class CandleAggregator:
    """Aggregates ticks into OHLCV candles for multiple intervals."""

    def __init__(
        self,
        intervals: Iterable[int] = (1, 5, 60),
        *,
        on_candle: OnCandleCallback | None = None,
    ) -> None:
        if not intervals:
            raise ValueError("At least one interval is required")
        self._intervals: Tuple[int, ...] = tuple(sorted(set(int(i) for i in intervals)))
        if any(interval <= 0 for interval in self._intervals):
            raise ValueError("Intervals must be positive integers (seconds)")
        self._buffers: Dict[int, MutableMapping[str, _CandleBuffer]] = {
            interval: {} for interval in self._intervals
        }
        self._queue: asyncio.Queue[CandlePayload] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._on_candle = on_candle

    async def handle_tick(self, tick: NormalizedTick) -> None:
        """Update candle buffers with a new tick."""
        async with self._lock:
            for interval in self._intervals:
                await self._process_interval(interval, tick)

    async def flush(self) -> None:
        """Emit any in-progress candles."""
        async with self._lock:
            for interval in self._intervals:
                buffers = self._buffers[interval]
                for symbol, candle in list(buffers.items()):
                    await self._emit(candle)
                    del buffers[symbol]

    async def next_candle(self) -> CandlePayload:
        """Await the next aggregated candle payload."""
        return await self._queue.get()

    def pending_candles(self) -> int:
        """Return the size of the candle queue (best effort)."""
        return self._queue.qsize()

    async def _process_interval(self, interval: int, tick: NormalizedTick) -> None:
        symbol_buffers = self._buffers[interval]
        bucket_start = self._bucket_start(tick.ts_utc, interval)

        current = symbol_buffers.get(tick.symbol)
        if current and bucket_start > current.open_time:
            # emit completed candle before starting a new bucket
            await self._emit(current)
            current = None

        if current is None:
            current = _CandleBuffer(
                symbol=tick.symbol,
                interval_seconds=interval,
                open_time=bucket_start,
                open=tick.price,
                high=tick.price,
                low=tick.price,
                close=tick.price,
                volume=0.0,
                last_tick_at=tick.ts_utc,
            )
            symbol_buffers[tick.symbol] = current

        current.update(tick.price, tick.volume, tick.ts_utc)

    async def _emit(self, candle: _CandleBuffer) -> None:
        payload = candle.to_payload()
        await self._queue.put(payload)
        if self._on_candle:
            result = self._on_candle(payload)
            if asyncio.iscoroutine(result):
                await result

    @staticmethod
    def _bucket_start(ts: datetime, interval: int) -> datetime:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        epoch_seconds = int(ts.timestamp())
        bucket = epoch_seconds - (epoch_seconds % interval)
        return datetime.fromtimestamp(bucket, tz=timezone.utc)


class TickAggregator:
    """
    Backwards-compatible wrapper that preserves the historic API used by
    ingestion scripts/tests while delegating candle emission to the
    `CandleAggregator`. It also adds a new 5-second interval buffer.
    """

    def __init__(
        self,
        flush_interval: int = 60,
        *,
        on_candle: OnCandleCallback | None = None,
    ) -> None:
        self.flush_interval = flush_interval
        self.candles_1s: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        self.candles_5s: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        self.candles_1m: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        self.lock = asyncio.Lock()
        self._candle_aggregator = CandleAggregator((1, 5, 60), on_candle=on_candle)

    async def aggregate_tick(self, tick: Dict[str, Any]) -> None:
        """Legacy entrypoint used by ingestion scripts (dict-based tick)."""
        symbol = tick["symbol"]
        timestamp = self._parse_timestamp(tick["ts_utc"])
        async with self.lock:
            self._aggregate_candle(self.candles_1s, symbol, timestamp, tick, 1)
            self._aggregate_candle(self.candles_5s, symbol, timestamp, tick, 5)
            self._aggregate_candle(self.candles_1m, symbol, timestamp, tick, 60)

        normalized = NormalizedTick(
            symbol=symbol,
            ts_utc=timestamp,
            price=float(tick.get("price", 0.0)),
            volume=float(tick.get("qty") or tick.get("volume") or 0.0),
            provider=str(tick.get("provider") or "custom"),
            raw=tick,
        )
        await self._candle_aggregator.handle_tick(normalized)

    async def flush_candles(self) -> None:
        async with self.lock:
            await self._flush_interval_candles(self.candles_1s, "1s")
            await self._flush_interval_candles(self.candles_5s, "5s")
            await self._flush_interval_candles(self.candles_1m, "1m")
        await self._candle_aggregator.flush()

    async def run(self) -> None:
        """Periodic flush loop for long running ingestion jobs."""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush_candles()

    def _aggregate_candle(
        self,
        candles: Dict[str, Dict[str, Dict[str, Any]]],
        symbol: str,
        timestamp: datetime,
        tick: Dict[str, Any],
        interval: int,
    ) -> None:
        bucket_key = self._get_bucket_key(timestamp, interval)
        store = candles[symbol]
        if bucket_key not in store:
            store[bucket_key] = {
                "symbol": symbol,
                "ts_utc": bucket_key,
                "open": tick["price"],
                "high": tick["price"],
                "low": tick["price"],
                "close": tick["price"],
                "volume": tick.get("qty", 0),
            }
        else:
            candle = store[bucket_key]
            candle["high"] = max(candle["high"], tick["price"])
            candle["low"] = min(candle["low"], tick["price"])
            candle["close"] = tick["price"]
            candle["volume"] += tick.get("qty", 0)

    def _get_bucket_key(self, timestamp: Any, interval: int) -> str:
        bucket_start = CandleAggregator._bucket_start(self._parse_timestamp(timestamp), interval)
        return bucket_start.isoformat()

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        if isinstance(value, str):
            cleaned = value.replace("Z", "+00:00")
            return datetime.fromisoformat(cleaned).astimezone(timezone.utc)
        raise ValueError(f"Unsupported timestamp type: {type(value)}")

    async def _flush_interval_candles(
        self,
        candles: Dict[str, Dict[str, Dict[str, Any]]],
        interval_label: str,
    ) -> None:
        for symbol, interval_candles in candles.items():
            for bucket_key, candle in interval_candles.items():
                try:
                    from market_data_ingestion.core.storage import DataStorage
                    import yaml
                    import os

                    config_path = os.path.join(
                        os.path.dirname(__file__), "..", "config", "config.example.yaml"
                    )
                    with open(config_path, "r", encoding="utf-8") as handle:
                        config = yaml.safe_load(handle)

                    storage = DataStorage(config["database"]["db_path"])
                    await storage.connect()
                    await storage.insert_candle(candle)
                    await storage.disconnect()
                    logger.info(
                        "Flushed %s candle for %s at %s",
                        interval_label,
                        symbol,
                        bucket_key,
                    )
                except Exception as exc:  # pragma: no cover - legacy path
                    logger.error("Failed to flush candle %s@%s: %s", symbol, bucket_key, exc)
            interval_candles.clear()
