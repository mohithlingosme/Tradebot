from __future__ import annotations

"""Exponential moving average crossover strategy."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from common.market_data import Candle
from strategies.base import Signal, Strategy
from strategies.registry import registry


@dataclass
class EMACrossoverConfig:
    short_window: int = 9
    long_window: int = 21
    timeframe: str = "5m"
    symbol_universe: List[str] = field(default_factory=lambda: ["NIFTY", "BANKNIFTY"])


class EMACrossoverStrategy(Strategy):
    """Simple long-only EMA crossover strategy."""

    def __init__(self, config: EMACrossoverConfig | dict | None = None) -> None:
        super().__init__()
        cfg = config or {}
        if isinstance(cfg, dict):
            cfg = EMACrossoverConfig(**cfg)
        self.config = cfg

        if self.config.short_window >= self.config.long_window:
            raise ValueError("short_window must be smaller than long_window")

        self.state.update({
            'short_multiplier': 2 / (self.config.short_window + 1),
            'long_multiplier': 2 / (self.config.long_window + 1),
            'short_ema': None,
            'long_ema': None,
            'position': 'flat',
            'last_signal': 'HOLD',
            'ema_history': [],
            'allowed_symbols': {symbol.upper() for symbol in self.config.symbol_universe}
        })

    def _update_ema(self, price: float, current: float | None, multiplier: float) -> float:
        if current is None:
            return price
        return (price - current) * multiplier + current

    def on_bar(self, bar: Candle, state: Dict[str, Any]) -> Signal:
        """Process a new bar and return a trading signal.

        Args:
            bar: The new candle/bar data.
            state: Mutable state dictionary for internal strategy state.

        Returns:
            Signal: 'BUY', 'SELL', or 'HOLD' based on strategy logic.
        """
        if state['allowed_symbols'] and bar.symbol.upper() not in state['allowed_symbols']:
            return 'HOLD'
        if bar.timeframe and bar.timeframe != self.config.timeframe:
            return 'HOLD'

        price = bar.close
        previous_short = state['short_ema']
        previous_long = state['long_ema']

        state['short_ema'] = self._update_ema(price, state['short_ema'], state['short_multiplier'])
        state['long_ema'] = self._update_ema(price, state['long_ema'], state['long_multiplier'])
        state['ema_history'].append((bar.timestamp, state['short_ema'], state['long_ema']))

        if previous_short is None or previous_long is None:
            return 'HOLD'

        prev_diff = previous_short - previous_long
        current_diff = state['short_ema'] - state['long_ema']

        if prev_diff <= 0 < current_diff and state['position'] != "long":
            state['position'] = "long"
            state['last_signal'] = "BUY"
            return "BUY"
        elif prev_diff >= 0 > current_diff and state['position'] == "long":
            state['position'] = "flat"
            state['last_signal'] = "SELL"
            return "SELL"

        return 'HOLD'

    @property
    def ema_history(self) -> List[tuple]:
        """Expose EMA values for testing and diagnostics."""
        return list(self.state['ema_history'])


# Register in the global registry for discovery
try:
    registry.register("ema_crossover_intraday_index", EMACrossoverStrategy)
except ValueError:
    # Allow re-imports in interactive sessions without failing
    pass

