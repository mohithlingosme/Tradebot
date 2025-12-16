#!/usr/bin/env python3
"""Unit tests for momentum and oscillator strategies."""

import unittest
import pandas as pd
import numpy as np
import backtrader as bt
from strategies.momentum import RSIStrategy, StochasticSlowStrategy, MomentumStrategy, TechnicalRatingStrategy


class TestMomentumStrategies(unittest.TestCase):
    """Test momentum and oscillator strategies."""

    def setUp(self):
        """Set up test data."""
        np.random.seed(42)  # For reproducible results

        # Generate sample OHLCV data
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        prices = np.cumsum(np.random.randn(50) * 2 + 0.1) + 100  # Trending up with volatility
        prices = np.maximum(prices, 10)  # Ensure positive prices

        self.data = pd.DataFrame({
            'open': prices * (1 + np.random.randn(50) * 0.01),
            'high': prices * (1 + np.random.randn(50) * 0.02),
            'low': prices * (1 - np.random.randn(50) * 0.02),
            'close': prices,
            'volume': np.random.randint(1000, 10000, 50)
        }, index=dates)

        # Ensure high >= close >= low and high >= open >= low
        self.data['high'] = np.maximum(self.data[['high', 'close', 'open']].max(axis=1), self.data['high'])
        self.data['low'] = np.minimum(self.data[['low', 'close', 'open']].min(axis=1), self.data['low'])

    def test_rsi_strategy(self):
        """Test RSI strategy."""
        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=self.data)
        cerebro.adddata(data)
        cerebro.addstrategy(RSIStrategy)
        cerebro.run()

        # Check that strategy ran without errors
        self.assertTrue(True)

    def test_stochastic_slow_strategy(self):
        """Test Stochastic Slow strategy."""
        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=self.data)
        cerebro.adddata(data)
        cerebro.addstrategy(StochasticSlowStrategy)
        cerebro.run()

        # Check that strategy ran without errors
        self.assertTrue(True)

    def test_momentum_strategy(self):
        """Test Momentum strategy."""
        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=self.data)
        cerebro.adddata(data)
        cerebro.addstrategy(MomentumStrategy)
        cerebro.run()

        # Check that strategy ran without errors
        self.assertTrue(True)

    def test_technical_rating_strategy(self):
        """Test Technical Rating strategy."""
        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=self.data)
        cerebro.adddata(data)
        cerebro.addstrategy(TechnicalRatingStrategy)
        cerebro.run()

        # Check that strategy ran without errors
        self.assertTrue(True)

    def test_strategy_parameters(self):
        """Test strategy parameters."""
        # Test RSI strategy with custom parameters
        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=self.data)
        cerebro.adddata(data)
        cerebro.addstrategy(RSIStrategy, period=21, overbought=75, oversold=25)
        cerebro.run()

        # Check that strategy ran without errors
        self.assertTrue(True)

    def test_insufficient_data(self):
        """Test behavior with insufficient data."""
        # Create small dataset that may not have enough data for indicators
        small_data = self.data.head(5)

        cerebro = bt.Cerebro()
        data = bt.feeds.PandasData(dataname=small_data)
        cerebro.adddata(data)

        # This should raise an IndexError when trying to access indicator values
        with self.assertRaises(IndexError):
            cerebro.addstrategy(RSIStrategy)
            cerebro.run()


if __name__ == '__main__':
    unittest.main()
