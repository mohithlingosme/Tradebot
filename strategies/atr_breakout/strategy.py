#!/usr/bin/env python3
"""ATR Breakout Strategy for FinBot."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from common.market_data import Candle
from strategies.base import Signal, Strategy
from strategies.registry import registry


@dataclass
class ATRBreakoutConfig:
    atr_period: int = 14
    breakout_multiplier: float = 2.0
    timeframe: str = "5m"
    symbol_universe: List[str] = field(default_factory=lambda: ["NIFTY", "BANKNIFTY"])


class ATRBreakoutStrategy(Strategy):
    """
    ATR Breakout Strategy.

    Logic:
    - Long: Enter when price breaks above (baseline + 2 × ATR)
    - Short: Enter when price breaks below (baseline - 2 × ATR)
    - Baseline: Simple moving average of closing prices
    - Exit: When price returns to baseline or opposite breakout occurs
    """

    def __init__(self, data_feed, config: ATRBreakoutConfig | dict | None = None) -> None:
        super().__init__(data_feed)
        cfg = config or {}
        if isinstance(cfg, dict):
            cfg = ATRBreakoutConfig(**cfg)
        self.config = cfg

        if self.config.atr_period < 1:
            raise ValueError("atr_period must be positive")
        if self.config.breakout_multiplier <= 0:
            raise ValueError("breakout_multiplier must be positive")

        self.state.update({
            'atr_period': self.config.atr_period,
            'breakout_multiplier': self.config.breakout_multiplier,
            'baseline_period': 20,  # Period for baseline SMA
            'position': 'flat',
            'last_signal': 'HOLD',
            'baseline_prices': [],
            'true_ranges': [],
            'atr_values': [],
            'baseline_sma': None,
            'current_atr': None,
            'upper_breakout': None,
            'lower_breakout': None,
            'allowed_symbols': {symbol.upper() for symbol in self.config.symbol_universe}
        })

    def _calculate_true_range(self, current: Candle, previous: Candle = None) -> float:
        """Calculate True Range for current candle."""
        if previous is None:
            # For first candle, use High - Low
            return current.high - current.low

        tr1 = current.high - current.low
        tr2 = abs(current.high - previous.close)
        tr3 = abs(current.low - previous.close)

        return max(tr1, tr2, tr3)

    def _update_atr(self, true_range: float) -> float:
        """Update ATR using Wilder's smoothing method."""
        if len(self.state['atr_values']) == 0:
            # First ATR value is simple average
            return true_range

        # Wilder's smoothing: ATR = (Previous ATR * (n-1) + Current TR) / n
        prev_atr = self.state['atr_values'][-1]
        return (prev_atr * (self.config.atr_period - 1) + true_range) / self.config.atr_period

    def _update_baseline(self, price: float) -> float:
        """Update baseline SMA."""
        self.state['baseline_prices'].append(price)
        if len(self.state['baseline_prices']) > self.state['baseline_period']:
            self.state['baseline_prices'].pop(0)

        if len(self.state['baseline_prices']) < self.state['baseline_period']:
            return None

        return sum(self.state['baseline_prices']) / len(self.state['baseline_prices'])

    def next(self) -> Signal:
        """Process the latest data and return a trading signal."""
        bar = self.data_feed.get_latest_bar()
        if not bar:
            return {'action': 'HOLD'}

        if self.state['allowed_symbols'] and bar.symbol.upper() not in self.state['allowed_symbols']:
            return {'action': 'HOLD'}
        if bar.timeframe and bar.timeframe != self.config.timeframe:
            return {'action': 'HOLD'}

        # Get previous bar for True Range calculation
        prev_bar = self.data_feed.get_previous_bar()
        true_range = self._calculate_true_range(bar, prev_bar)
        self.state['true_ranges'].append(true_range)

        # Update ATR
        current_atr = self._update_atr(true_range)
        self.state['atr_values'].append(current_atr)
        self.state['current_atr'] = current_atr

        # Update baseline
        baseline = self._update_baseline(bar.close)
        if baseline is None:
            return {'action': 'HOLD'}

        self.state['baseline_sma'] = baseline

        # Calculate breakout levels
        upper_breakout = baseline + (current_atr * self.config.breakout_multiplier)
        lower_breakout = baseline - (current_atr * self.config.breakout_multiplier)

        self.state['upper_breakout'] = upper_breakout
        self.state['lower_breakout'] = lower_breakout

        current_price = bar.close

        # Trading logic
        if self.state['position'] == 'flat':
            # Look for breakouts
            if current_price > upper_breakout:
                self.state['position'] = 'long'
                self.state['last_signal'] = 'BUY'
                return {'action': 'BUY', 'symbol': bar.symbol, 'price': bar.close, 'type': 'LIMIT'}
            elif current_price < lower_breakout:
                self.state['position'] = 'short'
                self.state['last_signal'] = 'SELL'
                return {'action': 'SELL', 'symbol': bar.symbol, 'price': bar.close, 'type': 'LIMIT'}

        elif self.state['position'] == 'long':
            # Exit long position when price returns to baseline or breaks lower
            if current_price <= baseline or current_price < lower_breakout:
                self.state['position'] = 'flat'
                self.state['last_signal'] = 'SELL'
                return {'action': 'SELL', 'symbol': bar.symbol, 'price': bar.close, 'type': 'LIMIT'}

        elif self.state['position'] == 'short':
            # Exit short position when price returns to baseline or breaks higher
            if current_price >= baseline or current_price > upper_breakout:
                self.state['position'] = 'flat'
                self.state['last_signal'] = 'BUY'
                return {'action': 'BUY', 'symbol': bar.symbol, 'price': bar.close, 'type': 'LIMIT'}

        return {'action': 'HOLD'}

    @property
    def atr_history(self) -> List[float]:
        """Expose ATR values for testing and diagnostics."""
        return list(self.state['atr_values'])

    @property
    def baseline_history(self) -> List[float]:
        """Expose baseline values for testing and diagnostics."""
        return list(self.state['baseline_prices'])


# Register in the global registry for discovery
try:
    registry.register("atr_breakout", ATRBreakoutStrategy)
except ValueError:
    # Allow re-imports in interactive sessions without failing
    pass
