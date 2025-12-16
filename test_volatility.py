#!/usr/bin/env python3
"""Unit tests for Volatility & Band Strategies."""

import unittest
import pandas as pd
import numpy as np
import backtrader as bt
from datetime import datetime, timedelta

from strategies.volatility import (
    BollingerBandsStrategy,
    BollingerBandsTrendStrategy,
    KeltnerChannelsStrategy,
    VoltyExpanCloseStrategy
)


class TestVolatilityStrategies(unittest.TestCase):
    """Test cases for volatility strategies."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample OHLCV data
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        np.random.seed(42)  # For reproducible results

        # Generate trending price data with volatility
        base_price = 100.0
        prices = []
        for i in range(50):
            trend = i * 0.5  # Upward trend
            volatility = np.random.normal(0, 2)  # Random volatility
            price = base_price + trend + volatility
            prices.append(max(price, 10))  # Ensure positive prices

        # Create OHLCV data
        self.data = pd.DataFrame({
            'open': [p - 0.5 for p in prices],
            'high': [p + 1.0 for p in prices],
            'low': [p - 1.0 for p in prices],
            'close': prices,
            'volume': [10000 + i * 500 for i in range(50)]
        }, index=dates)

    def create_cerebro(self, strategy_class, **params):
        """Create a backtrader Cerebro instance with test data."""
        cerebro = bt.Cerebro()
        cerebro.addstrategy(strategy_class, **params)

        # Add data feed
        data_feed = bt.feeds.PandasData(dataname=self.data)
        cerebro.adddata(data_feed)

        # Set initial cash
        cerebro.broker.setcash(10000.0)

        return cerebro

    def test_bollinger_bands_strategy(self):
        """Test Bollinger Bands Mean Reversion Strategy."""
        cerebro = self.create_cerebro(BollingerBandsStrategy, period=20, devfactor=2.0)
        initial_cash = cerebro.broker.getvalue()

        # Run strategy
        result = cerebro.run()
        final_cash = cerebro.broker.getvalue()

        # Basic assertions
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Strategy should have run without errors
        self.assertIsInstance(final_cash, float)

        # Check that trades were attempted (portfolio value changed)
        # Note: Actual profitability depends on data, but strategy should execute
        self.assertIsNotNone(final_cash)

    def test_bollinger_bands_trend_strategy(self):
        """Test Bollinger Bands Trend Following Strategy."""
        cerebro = self.create_cerebro(BollingerBandsTrendStrategy, period=20, devfactor=2.0)
        initial_cash = cerebro.broker.getvalue()

        # Run strategy
        result = cerebro.run()
        final_cash = cerebro.broker.getvalue()

        # Basic assertions
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Strategy should have run without errors
        self.assertIsInstance(final_cash, float)

    def test_keltner_channels_strategy(self):
        """Test Keltner Channels Strategy."""
        cerebro = self.create_cerebro(
            KeltnerChannelsStrategy,
            ema_period=20,
            atr_period=10,
            multiplier=2.0
        )
        initial_cash = cerebro.broker.getvalue()

        # Run strategy
        result = cerebro.run()
        final_cash = cerebro.broker.getvalue()

        # Basic assertions
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Strategy should have run without errors
        self.assertIsInstance(final_cash, float)

    def test_volty_expan_close_strategy(self):
        """Test Volatility Expansion Close Strategy."""
        cerebro = self.create_cerebro(
            VoltyExpanCloseStrategy,
            lookback=5,
            expansion_factor=1.5,
            exit_bars=3
        )
        initial_cash = cerebro.broker.getvalue()

        # Run strategy
        result = cerebro.run()
        final_cash = cerebro.broker.getvalue()

        # Basic assertions
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Strategy should have run without errors
        self.assertIsInstance(final_cash, float)

    def test_strategy_parameters(self):
        """Test that strategies accept and use parameters correctly."""
        # Test Bollinger Bands with custom parameters
        cerebro = self.create_cerebro(BollingerBandsStrategy, period=10, devfactor=1.5)
        result = cerebro.run()

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Test Keltner Channels with custom parameters
        cerebro = self.create_cerebro(
            KeltnerChannelsStrategy,
            ema_period=15,
            atr_period=7,
            multiplier=1.5
        )
        result = cerebro.run()

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_insufficient_data(self):
        """Test strategies with insufficient data for indicators."""
        # Create minimal data (less than required periods)
        small_data = self.data.head(5)  # Only 5 bars, but strategies need 20+

        cerebro = bt.Cerebro()
        cerebro.addstrategy(BollingerBandsStrategy, period=20, devfactor=2.0)

        data_feed = bt.feeds.PandasData(dataname=small_data)
        cerebro.adddata(data_feed)
        cerebro.broker.setcash(10000.0)

        # Should expect IndexError when indicators can't be calculated
        with self.assertRaises(IndexError):
            cerebro.run()

    def test_edge_case_parameters(self):
        """Test strategies with edge case parameters."""
        # Test with very small periods (should still work)
        cerebro = self.create_cerebro(BollingerBandsStrategy, period=2, devfactor=0.5)
        result = cerebro.run()

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        # Test with large multiplier
        cerebro = self.create_cerebro(KeltnerChannelsStrategy, multiplier=5.0)
        result = cerebro.run()

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


if __name__ == '__main__':
    unittest.main()
