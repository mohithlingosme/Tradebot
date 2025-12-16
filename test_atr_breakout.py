#!/usr/bin/env python3
"""Unit tests for ATR Breakout Strategy."""

import unittest
from unittest.mock import Mock
from datetime import datetime, timedelta

from strategies.atr_breakout.strategy import ATRBreakoutStrategy, ATRBreakoutConfig
from common.market_data import Candle


class MockDataFeed:
    """Mock data feed for testing."""

    def __init__(self, candles):
        self.candles = candles
        self.index = -1

    def get_latest_bar(self):
        if self.index < len(self.candles) - 1:
            self.index += 1
            return self.candles[self.index]
        return self.candles[-1] if self.candles else None

    def get_previous_bar(self):
        if self.index > 0:
            return self.candles[self.index - 1]
        return None


class TestATRBreakoutStrategy(unittest.TestCase):
    """Test cases for ATR Breakout Strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = ATRBreakoutConfig(
            atr_period=3,  # Shorter period for testing
            breakout_multiplier=2.0,
            symbol_universe=['NIFTY']
        )

    def create_test_candles(self):
        """Create test candle data."""
        base_time = datetime(2024, 1, 1, 9, 30)
        candles = []

        # Create trending data with some volatility
        prices = [100.0, 101.0, 102.5, 101.8, 103.2, 104.1, 102.9, 105.5, 106.2, 104.8,
                 107.1, 108.3, 106.7, 109.2, 110.1, 108.9, 111.5, 112.2, 110.8, 113.1]

        for i, price in enumerate(prices):
            timestamp = base_time + timedelta(minutes=i*5)
            # Create OHLC with some spread
            open_price = price - 0.5
            high = price + 1.0
            low = price - 1.0
            close = price
            volume = 10000 + (i * 500)

            candle = Candle(
                symbol='NIFTY',
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                timeframe='5m'
            )
            candles.append(candle)

        return candles

    def test_initialization(self):
        """Test strategy initialization."""
        data_feed = Mock()
        strategy = ATRBreakoutStrategy(data_feed, self.config)

        self.assertEqual(strategy.config.atr_period, 3)
        self.assertEqual(strategy.config.breakout_multiplier, 2.0)
        self.assertEqual(strategy.state['position'], 'flat')
        self.assertEqual(strategy.state['last_signal'], 'HOLD')

    def test_true_range_calculation(self):
        """Test True Range calculation."""
        data_feed = Mock()
        strategy = ATRBreakoutStrategy(data_feed, self.config)

        # Test first candle (no previous)
        candle1 = Candle(
            symbol='NIFTY',
            timestamp=datetime.now(),
            open=100,
            high=102,
            low=99,
            close=101,
            volume=1000,
            timeframe='5m'
        )
        tr1 = strategy._calculate_true_range(candle1)
        self.assertEqual(tr1, 3.0)  # High - Low

        # Test subsequent candle
        candle2 = Candle(
            symbol='NIFTY',
            timestamp=datetime.now(),
            open=101,
            high=103,
            low=100,
            close=102,
            volume=1000,
            timeframe='5m'
        )
        tr2 = strategy._calculate_true_range(candle2, candle1)
        expected_tr2 = max(3.0, abs(103-101), abs(100-101))  # max(TR1, |H2-C1|, |L2-C1|)
        self.assertEqual(tr2, expected_tr2)

    def test_atr_calculation(self):
        """Test ATR calculation with Wilder's smoothing."""
        data_feed = Mock()
        strategy = ATRBreakoutStrategy(data_feed, self.config)

        # First ATR (simple average)
        tr1, tr2, tr3 = 2.0, 2.5, 3.0
        atr1 = strategy._update_atr(tr1)
        strategy.state['atr_values'].append(atr1)  # Simulate state update
        self.assertEqual(atr1, 2.0)

        atr2 = strategy._update_atr(tr2)
        strategy.state['atr_values'].append(atr2)  # Simulate state update
        expected_atr2 = (2.0 * 2 + 2.5) / 3  # Wilder's smoothing
        self.assertAlmostEqual(atr2, expected_atr2, places=5)

        atr3 = strategy._update_atr(tr3)
        expected_atr3 = (expected_atr2 * 2 + 3.0) / 3
        self.assertAlmostEqual(atr3, expected_atr3, places=5)

    def test_baseline_calculation(self):
        """Test baseline SMA calculation."""
        data_feed = Mock()
        strategy = ATRBreakoutStrategy(data_feed, self.config)

        # Test with insufficient data
        baseline = strategy._update_baseline(100.0)
        self.assertIsNone(baseline)

        # Add more prices
        for price in [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0,
                     111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0]:
            baseline = strategy._update_baseline(price)

        # Should have 20 prices now
        self.assertIsNotNone(baseline)
        expected_baseline = sum(range(101, 121)) / 20  # Average of 101-120
        self.assertAlmostEqual(baseline, expected_baseline, places=5)

    def test_breakout_signal_generation(self):
        """Test breakout signal generation."""
        candles = self.create_test_candles()
        data_feed = MockDataFeed(candles)
        strategy = ATRBreakoutStrategy(data_feed, self.config)

        signals = []
        for _ in range(len(candles)):
            signal = strategy.next()
            signals.append(signal['action'])

        # Should generate some BUY signals (test data is trending upward)
        self.assertIn('BUY', signals)

        # Check that we have at least one BUY signal
        buy_count = signals.count('BUY')
        self.assertGreater(buy_count, 0)

    def test_position_management(self):
        """Test position state management."""
        candles = self.create_test_candles()
        data_feed = MockDataFeed(candles)
        strategy = ATRBreakoutStrategy(data_feed, self.config)

        # Process some candles
        for _ in range(10):
            strategy.next()

        # Check position state is valid
        valid_positions = ['flat', 'long', 'short']
        self.assertIn(strategy.state['position'], valid_positions)

        # Check last signal is valid
        valid_signals = ['HOLD', 'BUY', 'SELL']
        self.assertIn(strategy.state['last_signal'], valid_signals)

    def test_symbol_filtering(self):
        """Test symbol universe filtering."""
        config = ATRBreakoutConfig(symbol_universe=['NIFTY'])
        data_feed = Mock()
        strategy = ATRBreakoutStrategy(data_feed, config)

        # Mock candle for allowed symbol
        allowed_candle = Candle(
            symbol='NIFTY',
            timestamp=datetime.now(),
            open=100,
            high=101,
            low=99,
            close=100.5,
            volume=1000,
            timeframe='5m'
        )
        data_feed.get_latest_bar = Mock(return_value=allowed_candle)
        data_feed.get_previous_bar = Mock(return_value=None)

        signal = strategy.next()
        self.assertEqual(signal['action'], 'HOLD')  # Should be HOLD due to insufficient data

        # Mock candle for disallowed symbol
        disallowed_candle = Candle(
            symbol='BANKNIFTY',
            timestamp=datetime.now(),
            open=100,
            high=101,
            low=99,
            close=100.5,
            volume=1000,
            timeframe='5m'
        )
        data_feed.get_latest_bar = Mock(return_value=disallowed_candle)

        signal = strategy.next()
        self.assertEqual(signal['action'], 'HOLD')  # Should be HOLD due to symbol filter

    def test_timeframe_filtering(self):
        """Test timeframe filtering."""
        config = ATRBreakoutConfig(timeframe='5m')
        data_feed = Mock()
        strategy = ATRBreakoutStrategy(data_feed, config)

        # Mock candle with correct timeframe
        correct_tf_candle = Candle(
            symbol='NIFTY',
            timestamp=datetime.now(),
            open=100,
            high=101,
            low=99,
            close=100.5,
            volume=1000,
            timeframe='5m'
        )
        data_feed.get_latest_bar = Mock(return_value=correct_tf_candle)
        data_feed.get_previous_bar = Mock(return_value=None)

        signal = strategy.next()
        self.assertEqual(signal['action'], 'HOLD')  # Should be HOLD due to insufficient data

        # Mock candle with wrong timeframe
        wrong_tf_candle = Candle(
            symbol='NIFTY',
            timestamp=datetime.now(),
            open=100,
            high=101,
            low=99,
            close=100.5,
            volume=1000,
            timeframe='1m'
        )
        data_feed.get_latest_bar = Mock(return_value=wrong_tf_candle)

        signal = strategy.next()
        self.assertEqual(signal['action'], 'HOLD')  # Should be HOLD due to timeframe filter

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        data_feed = Mock()
        strategy = ATRBreakoutStrategy(data_feed, self.config)

        # Test with no data
        data_feed.get_latest_bar = Mock(return_value=None)
        signal = strategy.next()
        self.assertEqual(signal['action'], 'HOLD')

        # Test with invalid config
        with self.assertRaises(ValueError):
            invalid_config = ATRBreakoutConfig(atr_period=0)
            ATRBreakoutStrategy(data_feed, invalid_config)

        with self.assertRaises(ValueError):
            invalid_config = ATRBreakoutConfig(breakout_multiplier=-1.0)
            ATRBreakoutStrategy(data_feed, invalid_config)

    def test_signal_format(self):
        """Test signal format compliance."""
        candles = self.create_test_candles()
        data_feed = MockDataFeed(candles)
        strategy = ATRBreakoutStrategy(data_feed, self.config)

        # Process enough data to generate signals
        for _ in range(len(candles)):
            signal = strategy.next()
            if signal['action'] != 'HOLD':
                # Check signal format
                required_keys = ['action', 'symbol', 'price', 'type']
                for key in required_keys:
                    self.assertIn(key, signal)
                self.assertIn(signal['action'], ['BUY', 'SELL'])
                self.assertEqual(signal['type'], 'LIMIT')
                self.assertIsInstance(signal['price'], (int, float))


if __name__ == '__main__':
    unittest.main()
