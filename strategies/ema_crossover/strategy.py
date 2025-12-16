from __future__ import annotations

"""Exponential moving average crossover strategy."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from common.market_data import Candle
from strategies.base import Signal, Strategy
from strategies.registry import registry


@dataclass
class EMACrossoverConfig:
    short_window: int = 50
    long_window: int = 200
    timeframe: str = "5m"
    symbol_universe: List[str] = field(default_factory=lambda: ["NIFTY", "BANKNIFTY"])


class EMACrossoverStrategy(Strategy):
    """Simple long-only EMA crossover strategy."""

    def __init__(self, data_feed, config: EMACrossoverConfig | dict | None = None) -> None:
        super().__init__(data_feed)
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

    def next(self) -> Signal:
        """Process the latest data and return a trading signal.

        Returns:
            Signal: Standardized signal format {'action': 'BUY', 'symbol': 'INFY', 'price': 1500, 'type': 'LIMIT'}.
        """
        # Assuming data_feed provides the latest bar
        bar = self.data_feed.get_latest_bar()
        if not bar:
            return {'action': 'HOLD'}

        if self.state['allowed_symbols'] and bar.symbol.upper() not in self.state['allowed_symbols']:
            return {'action': 'HOLD'}
        if bar.timeframe and bar.timeframe != self.config.timeframe:
            return {'action': 'HOLD'}

        price = bar.close
        previous_short = self.state['short_ema']
        previous_long = self.state['long_ema']

        self.state['short_ema'] = self._update_ema(price, self.state['short_ema'], self.state['short_multiplier'])
        self.state['long_ema'] = self._update_ema(price, self.state['long_ema'], self.state['long_multiplier'])
        self.state['ema_history'].append((bar.timestamp, self.state['short_ema'], self.state['long_ema']))

        if previous_short is None or previous_long is None:
            return {'action': 'HOLD'}

        prev_diff = previous_short - previous_long
        current_diff = self.state['short_ema'] - self.state['long_ema']

        if prev_diff <= 0 < current_diff and self.state['position'] != "long":
            self.state['position'] = "long"
            self.state['last_signal'] = "BUY"
            return {'action': 'BUY', 'symbol': bar.symbol, 'price': bar.close, 'type': 'LIMIT'}
        elif prev_diff >= 0 > current_diff and self.state['position'] == "long":
            self.state['position'] = "flat"
            self.state['last_signal'] = "SELL"
            return {'action': 'SELL', 'symbol': bar.symbol, 'price': bar.close, 'type': 'LIMIT'}

        return {'action': 'HOLD'}

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

