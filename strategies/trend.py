#!/usr/bin/env python3
"""Trend Following Strategies for Backtrader."""

import backtrader as bt
from datetime import datetime


class SupertrendStrategy(bt.Strategy):
    """
    Supertrend Strategy.

    Logic: Standard Supertrend. Calculate Upper/Lower bands based on ATR.
    If Close > Upper Band, Trend = Bullish (Buy).
    If Close < Lower Band, Trend = Bearish (Sell).
    """

    params = (
        ('period', 10),
        ('multiplier', 3.0),
        ('printlog', False),
    )

    def __init__(self):
        self.atr = bt.indicators.ATR(self.data, period=self.params.period)
        self.hl2 = (self.data.high + self.data.low) / 2
        self.upperband = self.hl2 + (self.atr * self.params.multiplier)
        self.lowerband = self.hl2 - (self.atr * self.params.multiplier)
        self.trend = None

    def next(self):
        if self.data.close[0] > self.upperband[0]:
            if self.trend != 'bullish':
                self.trend = 'bullish'
                self.buy()
                self.log('BUY')
        elif self.data.close[0] < self.lowerband[0]:
            if self.trend != 'bearish':
                self.trend = 'bearish'
                self.sell()
                self.log('SELL')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} {txt}')


class ParabolicSARStrategy(bt.Strategy):
    """
    Parabolic SAR Strategy.

    Logic: Stop and Reverse system.
    Buy when SAR dots flip below price.
    Sell when SAR dots flip above price.
    """

    params = (
        ('start', 0.02),
        ('increment', 0.02),
        ('max', 0.2),
        ('printlog', False),
    )

    def __init__(self):
        self.sar = bt.indicators.ParabolicSAR(
            self.data,
            start=self.params.start,
            increment=self.params.increment,
            max=self.params.max
        )

    def next(self):
        if self.data.close[0] > self.sar[0] and self.data.close[-1] <= self.sar[-1]:
            self.buy()
            self.log('BUY')
        elif self.data.close[0] < self.sar[0] and self.data.close[-1] >= self.sar[-1]:
            self.sell()
            self.log('SELL')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} {txt}')


class MACDStrategy(bt.Strategy):
    """
    MACD Strategy.

    Logic:
    Buy when MACD line crosses above Signal line.
    Sell when MACD line crosses below Signal line.
    """

    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
        ('printlog', False),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        if self.crossover > 0:
            self.buy()
            self.log('BUY')
        elif self.crossover < 0:
            self.sell()
            self.log('SELL')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} {txt}')


class MovingAverageCrossSingle(bt.Strategy):
    """
    Moving Average Cross (Single Line) Strategy.

    Logic:
    Buy when Close > MA.
    Sell when Close < MA.
    """

    params = (
        ('ma_type', 'SMA'),
        ('period', 50),
        ('printlog', False),
    )

    def __init__(self):
        if self.params.ma_type.upper() == 'SMA':
            self.ma = bt.indicators.SMA(self.data.close, period=self.params.period)
        elif self.params.ma_type.upper() == 'EMA':
            self.ma = bt.indicators.EMA(self.data.close, period=self.params.period)
        else:
            raise ValueError("ma_type must be 'SMA' or 'EMA'")

    def next(self):
        if self.data.close[0] > self.ma[0]:
            self.buy()
            self.log('BUY')
        elif self.data.close[0] < self.ma[0]:
            self.sell()
            self.log('SELL')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} {txt}')


class MovingAverageCross2LineStrategy(bt.Strategy):
    """
    Moving Average Cross (2-Line) Strategy.
    Logic: Golden Cross / Death Cross.
    Buy: Fast MA crosses above Slow MA.
    Sell: Fast MA crosses below Slow MA.
    """
    params = (
        ('fast_period', 50),
        ('slow_period', 200),
        ('ma_type', 'SMA'),
        ('printlog', False),
    )

    def __init__(self):
        ma_map = {
            'SMA': bt.indicators.SMA,
            'EMA': bt.indicators.EMA,
        }
        ma_indicator = ma_map.get(self.params.ma_type.upper(), bt.indicators.SMA)

        self.fast_ma = ma_indicator(self.data.close, period=self.params.fast_period)
        self.slow_ma = ma_indicator(self.data.close, period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if self.crossover > 0:  # Fast MA crosses above Slow MA
            if not self.position:
                self.buy()
                self.log(f'BUY CREATE, {self.data.close[0]:.2f}')
        elif self.crossover < 0:  # Fast MA crosses below Slow MA
            if self.position:
                self.close()
                self.log(f'SELL CREATE, {self.data.close[0]:.2f}')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} - {txt}')


class RobBookerADXBreakoutStrategy(bt.Strategy):
    """
    Rob Booker ADX Breakout Strategy.
    Logic:
    Buy: If ADX > Threshold AND +DI > -DI.
    Sell: If ADX > Threshold AND -DI > +DI.
    """
    params = (
        ('period', 14),
        ('threshold', 30),
        ('printlog', False),
    )

    def __init__(self):
        self.adx = bt.indicators.ADX(self.data, period=self.params.period)

    def next(self):
        if self.adx.adx[0] > self.params.threshold:
            if self.adx.plusdi[0] > self.adx.minusdi[0]:
                if not self.position:
                    self.buy()
                    self.log(f'BUY CREATE, {self.data.close[0]:.2f}')
            elif self.adx.minusdi[0] > self.adx.plusdi[0]:
                if self.position:
                    self.close()
                    self.log(f'SELL CREATE, {self.data.close[0]:.2f}')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} - {txt}')


class PriceChannelStrategy(bt.Strategy):
    """
    Price Channel (Donchian Channel) Strategy.
    Logic:
    Buy: Price closes > Highest High of last period.
    Sell: Price closes < Lowest Low of last period.
    """
    params = (
        ('period', 20),
        ('printlog', False),
    )

    def __init__(self):
        self.highest_high = bt.indicators.Highest(self.data.high, period=self.params.period, plot=False)
        self.lowest_low = bt.indicators.Lowest(self.data.low, period=self.params.period, plot=False)

    def next(self):
        # The channel is for the previous N bars, so we use [-1]
        if self.data.close[0] > self.highest_high[-1]:
            if not self.position:
                self.buy()
                self.log(f'BUY CREATE, {self.data.close[0]:.2f}')
        elif self.data.close[0] < self.lowest_low[-1]:
            if self.position:
                self.close()
                self.log(f'SELL CREATE, {self.data.close[0]:.2f}')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} - {txt}')


class ChannelBreakoutStrategy(bt.Strategy):
    """
    Channel Breakout Strategy.
    A variation of Price Channel with a filter.
    Buy: Price > Highest(High, period) AND Close > Open (Green Candle).
    Sell: Price < Lowest(Low, period) AND Close < Open (Red Candle).
    """
    params = (
        ('period', 20),
        ('printlog', False),
    )

    def __init__(self):
        self.highest_high = bt.indicators.Highest(self.data.high, period=self.params.period, plot=False)
        self.lowest_low = bt.indicators.Lowest(self.data.low, period=self.params.period, plot=False)

    def next(self):
        is_green_candle = self.data.close[0] > self.data.open[0]
        is_red_candle = self.data.close[0] < self.data.open[0]

        # The breakout is compared to the channel of the PREVIOUS bars.
        if self.data.high[0] > self.highest_high[-1] and is_green_candle:
            if not self.position:
                self.buy()
                self.log(f'BUY CREATE, {self.data.close[0]:.2f}')
        elif self.data.low[0] < self.lowest_low[-1] and is_red_candle:
            if self.position:
                self.close()
                self.log(f'SELL CREATE, {self.data.close[0]:.2f}')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} - {txt}')


class PivotExtensionStrategy(bt.Strategy):
    """
    Pivot Extension Strategy.
    Logic:
    Internally calculates Standard Daily Pivots.
    Buy: Close > R1.
    Sell: Close < S1.
    Note: This requires a daily data feed (or higher) to be added to cerebro,
          or a custom implementation for intraday calculation.
          This implementation uses backtrader's standard PivotPoint indicator.
    """
    params = (
        ('lookback', 15), # Standard lookback for daily pivots on intraday data
        ('printlog', False),
    )

    def __init__(self):
        # This indicator automatically calculates pivots.
        # It needs to know the timeframe of the data (e.g., daily, weekly).
        # For intraday, you'd typically resample or use a higher timeframe data feed.
        # Assuming the main data feed is what we operate on.
        self.pivots = bt.indicators.PivotPoint(self.data)

    def next(self):
        if not self.position:
            if self.data.close[0] > self.pivots.r1[0]:
                self.buy()
                self.log(f'BUY CREATE > R1, {self.data.close[0]:.2f}')
        else:
            if self.data.close[0] < self.pivots.s1[0]:
                self.close()
                self.log(f'SELL CREATE < S1, {self.data.close[0]:.2f}')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        if self.params.printlog:
            print(f'{dt.isoformat()} - {txt}')
