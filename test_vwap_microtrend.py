#!/usr/bin/env python3
"""Thorough testing script for VWAP Microtrend Strategy."""

import sys
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

# Add strategies to path
sys.path.append('strategies')

from strategies.vwap_microtrend.strategy import VWAPMicrotrendStrategy, VWAPMicrotrendConfig
from common.market_data import Candle


@dataclass
class MockDataFeed:
    """Mock data feed for testing."""
    bars: List[Candle]
    current_index: int = 0

    def get_latest_bar(self) -> Optional[Candle]:
        if self.current_index < len(self.bars):
            bar = self.bars[self.current_index]
            self.current_index += 1
            return bar
        return None


def create_test_bars() -> List[Candle]:
    """Create test bars with known VWAP and trend scenarios."""
    base_time = datetime(2024, 1, 1, 9, 15)  # Market open
    bars = []

    # Create bars with prices and volumes that will create known VWAP values
    # Start with uptrend, then downtrend
    test_data = [
        # Time, Open, High, Low, Close, Volume
        (0, 100.0, 101.0, 99.5, 100.5, 100000),  # First bar after open
        (5, 100.5, 102.0, 100.0, 101.5, 120000),  # Uptrend continues
        (10, 101.5, 103.0, 101.0, 102.5, 110000), # Uptrend
        (15, 102.5, 104.0, 102.0, 103.5, 130000), # Past buffer, uptrend
        (20, 103.5, 105.0, 103.0, 104.5, 125000), # Strong uptrend
        (25, 104.5, 106.0, 104.0, 105.5, 140000), # Peak
        (30, 105.5, 105.0, 103.5, 104.0, 115000), # Start downtrend
        (35, 104.0, 104.5, 102.5, 103.0, 120000), # Downtrend
        (40, 103.0, 103.5, 101.5, 102.0, 110000), # Downtrend continues
        (45, 102.0, 102.5, 100.5, 101.0, 105000), # Downtrend
    ]

    for minutes, open_p, high, low, close, volume in test_data:
        timestamp = base_time + timedelta(minutes=minutes)
        bar = Candle(
            timestamp=timestamp,
            symbol="NIFTY",
            timeframe="5m",
            open=open_p,
            high=high,
            low=low,
            close=close,
            volume=volume
        )
        bars.append(bar)

    return bars


def test_vwap_calculation():
    """Test VWAP calculation accuracy."""
    print("Testing VWAP calculation accuracy...")

    bars = create_test_bars()
    data_feed = MockDataFeed(bars)
    strategy = VWAPMicrotrendStrategy(data_feed)

    # Run strategy through all bars
    for _ in range(len(bars)):
        strategy.next()

    # Calculate expected VWAP manually
    cumulative_pv = 0.0
    cumulative_vol = 0.0

    for bar in bars:
        typical_price = (bar.high + bar.low + bar.close) / 3
        cumulative_pv += typical_price * bar.volume
        cumulative_vol += bar.volume

    expected_vwap = cumulative_pv / cumulative_vol
    actual_vwap = strategy.state['vwap']

    print(".4f")
    print(".4f")

    assert abs(actual_vwap - expected_vwap) < 0.001, f"VWAP mismatch: expected {expected_vwap}, got {actual_vwap}"
    print("✓ VWAP calculation accurate.\n")


def test_trend_detection():
    """Test trend detection logic."""
    print("Testing trend detection logic...")

    bars = create_test_bars()
    data_feed = MockDataFeed(bars)
    strategy = VWAPMicrotrendStrategy(data_feed)

    # Run through bars and collect trend states
    trends = []
    for _ in range(len(bars)):
        strategy.next()
        if len(strategy.state['trend_history']) >= 2:
            prev_trend = strategy.state['trend_history'][-2]
            curr_trend = strategy.state['trend_history'][-1]
            trend_direction = strategy._detect_trend(curr_trend, prev_trend)
            trends.append(trend_direction)

    # Should see up trends early, then down trends later
    assert 'up' in trends, "Should detect upward trends"
    assert 'down' in trends, "Should detect downward trends"
    print("✓ Trend detection working.\n")


def test_market_open_filter():
    """Test market open buffer filter."""
    print("Testing market open buffer filter...")

    bars = create_test_bars()  # First bar at 9:15, buffer is 15 mins
    data_feed = MockDataFeed(bars)
    strategy = VWAPMicrotrendStrategy(data_feed)

    # First few bars should be filtered (within 15 min buffer)
    signals = []
    for i in range(4):  # First 4 bars (9:15, 9:20, 9:25, 9:30)
        signal = strategy.next()
        signals.append(signal)

    # All signals in buffer period should be HOLD
    for signal in signals[:3]:  # First 3 bars are within buffer
        assert signal['action'] == 'HOLD', f"Expected HOLD in buffer period, got {signal}"

    print("✓ Market open filter working.\n")


def test_signal_generation():
    """Test buy/sell signal generation."""
    print("Testing signal generation...")

    bars = create_test_bars()
    data_feed = MockDataFeed(bars)
    strategy = VWAPMicrotrendStrategy(data_feed)

    signals = []
    for _ in range(len(bars)):
        signal = strategy.next()
        signals.append(signal)

    # Should have some BUY and SELL signals after buffer period
    buy_signals = [s for s in signals if s.get('action') == 'BUY']
    sell_signals = [s for s in signals if s.get('action') == 'SELL']

    print(f"Found {len(buy_signals)} BUY signals and {len(sell_signals)} SELL signals")

    # Verify signal format
    for signal in buy_signals + sell_signals:
        required_keys = {'action', 'symbol', 'price', 'type'}
        assert set(signal.keys()) == required_keys, f"Signal missing keys: {signal}"
        assert signal['action'] in ['BUY', 'SELL'], f"Invalid action: {signal['action']}"
        assert signal['symbol'] == 'NIFTY', f"Wrong symbol: {signal['symbol']}"
        assert signal['type'] == 'LIMIT', f"Wrong type: {signal['type']}"
        assert isinstance(signal['price'], (int, float)), f"Price not numeric: {signal['price']}"

    print("✓ Signal generation and format correct.\n")


def test_edge_cases():
    """Test edge cases: no data, insufficient data, etc."""
    print("Testing edge cases...")

    # Test with no bars
    empty_feed = MockDataFeed([])
    strategy = VWAPMicrotrendStrategy(empty_feed)
    signal = strategy.next()
    assert signal == {'action': 'HOLD'}, f"Expected HOLD for no data, got {signal}"

    # Test with single bar
    single_bar = [create_test_bars()[0]]
    single_feed = MockDataFeed(single_bar)
    strategy = VWAPMicrotrendStrategy(single_feed)
    signal = strategy.next()
    assert signal == {'action': 'HOLD'}, f"Expected HOLD for single bar, got {signal}"

    print("✓ Edge cases handled correctly.\n")


def main():
    """Run all tests."""
    print("Starting thorough testing of VWAP Microtrend Strategy...\n")

    try:
        test_vwap_calculation()
        test_trend_detection()
        test_market_open_filter()
        test_signal_generation()
        test_edge_cases()

        print("🎉 All tests passed! VWAP Microtrend Strategy is working correctly.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
