#!/usr/bin/env python3
"""Backtrader-compatible VWAP Microtrend Strategy."""

import backtrader as bt
from datetime import time


class VWAPMicrotrendStrategy(bt.Strategy):
    """
    VWAP Microtrend Strategy for Backtrader.

    Logic:
    - Long if Price > VWAP AND Trend is Up (short EMA > previous short EMA)
    - Short if Price < VWAP AND Trend is Down (short EMA < previous short EMA)
    - Filter: Avoid trading during first 15 mins (Market Open Volatility)
    """

    params = (
        ('trend_period', 5),  # Period for trend detection (short EMA)
        ('market_open_buffer_minutes', 15),  # Skip trading first N minutes
        ('printlog', False),
    )

    def __init__(self):
        # VWAP calculation
        self.vwap = bt.indicators.VWAP(self.data)

        # Trend EMA (short-term)
        self.trend_ema = bt.indicators.EMA(self.data.close, period=self.params.trend_period)

        # Previous values for crossover detection
        self.prev_trend_ema = None

        # Position tracking
        self.position_size = 0

    def next(self):
        # Market open buffer filter
        if self._is_market_open_buffer():
            return

        current_price = self.data.close[0]
        current_vwap = self.vwap[0]
        current_trend = self.trend_ema[0]

        # Detect trend direction
        trend_direction = self._detect_trend(current_trend, self.prev_trend_ema)

        # Trading logic
        if trend_direction == 'up' and current_price > current_vwap and self.position_size <= 0:
            # Go long
            self.buy(size=1)
            self.position_size = 1
            if self.params.printlog:
                self.log(f'BUY at {current_price:.2f}')

        elif trend_direction == 'down' and current_price < current_vwap and self.position_size > 0:
            # Close long position
            self.sell(size=1)
            self.position_size = 0
            if self.params.printlog:
                self.log(f'SELL at {current_price:.2f}')

        # Update previous trend value
        self.prev_trend_ema = current_trend

    def _is_market_open_buffer(self):
        """Check if we're within the market open buffer period."""
        current_time = self.data.datetime.time()

        # Assume market opens at 9:15 AM
        market_open = time(9, 15)
        current_minutes = current_time.hour * 60 + current_time.minute
        open_minutes = market_open.hour * 60 + market_open.minute
        minutes_since_open = current_minutes - open_minutes

        return minutes_since_open < self.params.market_open_buffer_minutes

    def _detect_trend(self, current_trend, previous_trend):
        """Detect trend direction based on EMA movement."""
        if previous_trend is None:
            return 'neutral'

        if current_trend > previous_trend:
            return 'up'
        elif current_trend < previous_trend:
            return 'down'
        else:
            return 'neutral'

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
