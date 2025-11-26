from __future__ import annotations

"""Exponential moving average crossover strategy."""

from dataclasses import dataclass, field
from typing import List

from common.market_data import Candle
from strategies.base import Signal, Strategy
from strategies.registry import registry


@dataclass
class EMACrossoverConfig:
    short_window: int = 9
    long_window: int = 21
    timeframe: str = "5m"
    symbol_universe: List[str] = field(default_factory=lambda: ["NIFTY", "BANKNIFTY"])


class EMACrossoverStrategy:
    """Simple long-only EMA crossover strategy."""

    def __init__(self, config: EMACrossoverConfig | dict | None = None) -> None:
        cfg = config or {}
        if isinstance(cfg, dict):
            cfg = EMACrossoverConfig(**cfg)
        self.config = cfg

        if self.config.short_window >= self.config.long_window:
            raise ValueError("short_window must be smaller than long_window")

        self.short_multiplier = 2 / (self.config.short_window + 1)
        self.long_multiplier = 2 / (self.config.long_window + 1)

        self.short_ema: float | None = None
        self.long_ema: float | None = None
        self.position: str = "flat"
        self._last_signal: Signal = "NONE"
        self._ema_history: List[tuple] = []
        self._allowed_symbols = {symbol.upper() for symbol in self.config.symbol_universe}

    def _update_ema(self, price: float, current: float | None, multiplier: float) -> float:
        if current is None:
            return price
        return (price - current) * multiplier + current

    def update(self, candle: Candle) -> None:
        """Ingest the next candle and update indicator state."""
        if self._allowed_symbols and candle.symbol.upper() not in self._allowed_symbols:
            return
        if candle.timeframe and candle.timeframe != self.config.timeframe:
            return

        price = candle.close
        previous_short = self.short_ema
        previous_long = self.long_ema

        self.short_ema = self._update_ema(price, self.short_ema, self.short_multiplier)
        self.long_ema = self._update_ema(price, self.long_ema, self.long_multiplier)
        self._ema_history.append((candle.timestamp, self.short_ema, self.long_ema))

        self._last_signal = "NONE"
        if previous_short is None or previous_long is None:
            return

        prev_diff = previous_short - previous_long
        current_diff = self.short_ema - self.long_ema

        if prev_diff <= 0 < current_diff and self.position != "long":
            self.position = "long"
            self._last_signal = "BUY"
        elif prev_diff >= 0 > current_diff and self.position == "long":
            self.position = "flat"
            self._last_signal = "SELL"

    def signal(self) -> Signal:
        """Return the latest trading signal."""
        return self._last_signal

    @property
    def ema_history(self) -> List[tuple]:
        """Expose EMA values for testing and diagnostics."""
        return list(self._ema_history)


# Register in the global registry for discovery
try:
    registry.register("ema_crossover_intraday_index", EMACrossoverStrategy)
except ValueError:
    # Allow re-imports in interactive sessions without failing
    pass

