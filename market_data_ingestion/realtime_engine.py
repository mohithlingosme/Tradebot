from __future__ import annotations

"""Realtime market data engine that ties adapters and aggregators together."""

import asyncio
import contextlib
from typing import Awaitable, Callable, Dict, Iterable, List, Optional

from market_data_ingestion.adapters import get_adapter
from market_data_ingestion.adapters.base import BaseMarketDataAdapter, NormalizedTick
from market_data_ingestion.core.aggregator import CandleAggregator, CandlePayload
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)

OnTick = Callable[[NormalizedTick], Awaitable[None] | None]
OnCandle = Callable[[CandlePayload], Awaitable[None] | None]


class MarketDataEngine:
    """Streams ticks from an adapter and surfaces aggregated candles."""

    def __init__(
        self,
        adapter_name: str,
        adapter_config: Dict[str, object],
        *,
        candle_intervals: Iterable[int] = (1, 5, 60),
        on_tick: OnTick | None = None,
        on_candle: OnCandle | None = None,
    ) -> None:
        self._adapter_name = adapter_name
        self._adapter_config = adapter_config
        self._adapter: Optional[BaseMarketDataAdapter] = None
        self._on_tick = on_tick
        self._aggregator = CandleAggregator(candle_intervals, on_candle=on_candle)
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()

    async def start(self, symbols: List[str]) -> None:
        if self._task:
            raise RuntimeError("Engine already running")
        self._adapter = get_adapter(self._adapter_name, self._adapter_config)
        await self._adapter.subscribe(symbols)
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        if self._adapter:
            await self._adapter.close()
            self._adapter = None
        await self._aggregator.flush()

    async def _run(self) -> None:
        assert self._adapter is not None
        async for tick in self._adapter.stream():
            if self._stop_event.is_set():
                break
            await self._handle_tick(tick)

    async def _handle_tick(self, tick: NormalizedTick) -> None:
        if self._on_tick:
            result = self._on_tick(tick)
            if asyncio.iscoroutine(result):
                await result
        await self._aggregator.handle_tick(tick)

    async def next_candle(self) -> CandlePayload:
        return await self._aggregator.next_candle()
