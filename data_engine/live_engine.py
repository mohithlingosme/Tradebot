from __future__ import annotations

"""Tick-to-candle streaming helper."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict, Optional, Tuple

from .candle import Candle
from .logger import CSVLogger
from .rolling import RollingWindow

logger = logging.getLogger(__name__)

OnCandleCallback = Callable[[Candle], None]


class LiveDataEngine:
    """
    Convert ticks into completed candles with optional CSV logging.
    """

    def __init__(
        self,
        timeframe_s: int,
        window_size: int,
        logger: CSVLogger | None = None,
        on_candle: OnCandleCallback | None = None,
    ):
        if timeframe_s <= 0:
            raise ValueError("timeframe_s must be positive")
        self.timeframe_s = timeframe_s
        self.logger = logger
        self._on_candle = on_candle
        self._current: Dict[str, Candle] = {}
        self._windows: Dict[str, RollingWindow[Candle]] = defaultdict(lambda: RollingWindow(window_size))

    def on_tick(
        self,
        symbol: str,
        ts: datetime,
        price: float,
        volume: float | None = None,
    ) -> Tuple[Candle, Optional[Candle]]:
        """
        Process a tick and return the current candle plus a completed candle (if any).
        """
        if self.logger:
            self.logger.log_tick(symbol, ts, price, volume or 0.0)

        current = self._current.get(symbol)
        completed: Optional[Candle] = None

        if current is None:
            current = Candle.from_tick(symbol, self.timeframe_s, ts, price, volume)
            self._current[symbol] = current
            logger.debug("Started candle %s", current)
            return current, None

        if current.is_complete(ts):
            completed = current
            self._append_candle(symbol, completed)
            if self._on_candle:
                self._on_candle(completed)
            logger.debug("Closed candle %s", completed)

            current = Candle.from_tick(symbol, self.timeframe_s, ts, price, volume)
            self._current[symbol] = current
            logger.debug("Started candle %s", current)
            return current, completed

        current.update(price, volume, ts)
        return current, completed

    def _append_candle(self, symbol: str, candle: Candle) -> None:
        window = self._windows[symbol]
        window.append(candle)

    def window(self, symbol: str) -> RollingWindow[Candle]:
        """
        Access the rolling window for a given symbol.
        """
        return self._windows[symbol]
