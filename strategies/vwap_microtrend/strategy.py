from __future__ import annotations

"""VWAP Microtrend strategy for intraday trading."""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime, time

from common.market_data import Candle
from strategies.base import Signal, Strategy
from strategies.registry import registry


@dataclass
class VWAPMicrotrendConfig:
    """Configuration for VWAP Microtrend strategy."""
    trend_period: int = 5  # Period for trend detection (short EMA)
    vwap_anchor: str = "session"  # "session" for daily VWAP, or "anchored" for custom anchor
    market_open_buffer_minutes: int = 15  # Skip trading first N minutes after market open
    symbol_universe: List[str] = field(default_factory=lambda: ["NIFTY", "BANKNIFTY"])
    timeframe: str = "5m"


class VWAPMicrotrendStrategy(Strategy):
    """
    VWAP Microtrend Strategy.

    Logic:
    - Long if Price > VWAP AND Trend is Up (short EMA > previous short EMA)
    - Short if Price < VWAP AND Trend is Down (short EMA < previous short EMA)
    - Filter: Avoid trading during first 15 mins (Market Open Volatility)
    """

    def __init__(self, data_feed, config: VWAPMicrotrendConfig | dict | None = None) -> None:
        super().__init__(data_feed)
        cfg = config or {}
        if isinstance(cfg, dict):
            cfg = VWAPMicrotrendConfig(**cfg)
        self.config = cfg

        # Initialize state
        self.state.update({
            'trend_multiplier': 2 / (self.config.trend_period + 1),
            'trend_ema': None,
            'vwap': None,
            'cumulative_price_volume': 0.0,
            'cumulative_volume': 0.0,
            'session_start': None,
            'position': 'flat',
            'last_signal': 'HOLD',
            'allowed_symbols': {symbol.upper() for symbol in self.config.symbol_universe},
            'price_history': [],
            'trend_history': []
        })

    def _is_market_open_buffer(self, timestamp: datetime) -> bool:
        """Check if we're within the market open buffer period."""
        if not timestamp:
            return True

        # Assume market opens at 9:15 AM IST (common for Indian markets)
        market_open = time(9, 15)
        current_time = timestamp.time()

        # Calculate minutes since market open
        open_minutes = market_open.hour * 60 + market_open.minute
        current_minutes = current_time.hour * 60 + current_time.minute
        minutes_since_open = current_minutes - open_minutes

        return minutes_since_open < self.config.market_open_buffer_minutes

    def _update_trend_ema(self, price: float) -> float:
        """Update the trend EMA (short-term moving average)."""
        if self.state['trend_ema'] is None:
            return price
        return (price - self.state['trend_ema']) * self.state['trend_multiplier'] + self.state['trend_ema']

    def _update_vwap(self, high: float, low: float, close: float, volume: float) -> float:
        """Update VWAP calculation."""
        # Use typical price (H+L+C)/3 for VWAP calculation
        typical_price = (high + low + close) / 3
        price_volume = typical_price * volume

        self.state['cumulative_price_volume'] += price_volume
        self.state['cumulative_volume'] += volume

        if self.state['cumulative_volume'] > 0:
            return self.state['cumulative_price_volume'] / self.state['cumulative_volume']
        return typical_price

    def _detect_trend(self, current_trend_ema: float, previous_trend_ema: float | None) -> str:
        """Detect trend direction based on EMA movement."""
        if previous_trend_ema is None:
            return 'neutral'

        if current_trend_ema > previous_trend_ema:
            return 'up'
        elif current_trend_ema < previous_trend_ema:
            return 'down'
        else:
            return 'neutral'

    def _reset_session_data(self, timestamp: datetime):
        """Reset VWAP calculation for new trading session."""
        current_date = timestamp.date()
        # Reset if this is the first bar or a new trading day
        if self.state['session_start'] is None or current_date != self.state['session_start']:
            self.state.update({
                'vwap': None,
                'cumulative_price_volume': 0.0,
                'cumulative_volume': 0.0,
                'session_start': current_date
            })

    def next(self) -> Signal:
        """Process the latest data and return a trading signal."""
        bar = self.data_feed.get_latest_bar()
        if not bar:
            return {'action': 'HOLD'}

        # Symbol and timeframe filters
        if self.state['allowed_symbols'] and bar.symbol.upper() not in self.state['allowed_symbols']:
            return {'action': 'HOLD'}
        if bar.timeframe and bar.timeframe != self.config.timeframe:
            return {'action': 'HOLD'}

        # Market open buffer filter
        if self._is_market_open_buffer(bar.timestamp):
            return {'action': 'HOLD'}

        # Reset session data if needed
        self._reset_session_data(bar.timestamp)

        # Update trend EMA
        previous_trend_ema = self.state['trend_ema']
        self.state['trend_ema'] = self._update_trend_ema(bar.close)

        # Update VWAP
        self.state['vwap'] = self._update_vwap(bar.high, bar.low, bar.close, bar.volume)

        # Store history for debugging
        self.state['price_history'].append(bar.close)
        self.state['trend_history'].append(self.state['trend_ema'])

        # Need enough data for calculations
        if previous_trend_ema is None or self.state['vwap'] is None:
            return {'action': 'HOLD'}

        # Detect trend
        trend = self._detect_trend(self.state['trend_ema'], previous_trend_ema)

        # Trading logic
        price = bar.close
        vwap = self.state['vwap']

        # Long signal: Price > VWAP and trend is up
        if price > vwap and trend == 'up' and self.state['position'] != 'long':
            self.state['position'] = 'long'
            self.state['last_signal'] = 'BUY'
            return {
                'action': 'BUY',
                'symbol': bar.symbol,
                'price': bar.close,
                'type': 'LIMIT'
            }

        # Short signal: Price < VWAP and trend is down
        elif price < vwap and trend == 'down' and self.state['position'] == 'long':
            self.state['position'] = 'flat'
            self.state['last_signal'] = 'SELL'
            return {
                'action': 'SELL',
                'symbol': bar.symbol,
                'price': bar.close,
                'type': 'LIMIT'
            }

        return {'action': 'HOLD'}

    @property
    def vwap_history(self) -> List[float]:
        """Expose VWAP values for testing and diagnostics."""
        # This would need to be stored in state if we want full history
        return [self.state['vwap']] if self.state['vwap'] is not None else []

    @property
    def trend_history(self) -> List[float]:
        """Expose trend EMA values for testing and diagnostics."""
        return list(self.state['trend_history'])


# Register in the global registry for discovery
try:
    registry.register("vwap_microtrend", VWAPMicrotrendStrategy)
except ValueError:
    # Allow re-imports in interactive sessions without failing
    pass
