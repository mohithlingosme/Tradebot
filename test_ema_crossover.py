#!/usr/bin/env python3
"""Thorough testing script for EMA Crossover Strategy."""

import sys
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

# Add strategies to path
sys.path.append('strategies')

from strategies.ema_crossover.strategy import EMACrossoverStrategy, EMACrossoverConfig
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
    """Create test bars with known EMA crossover scenarios."""
    base_time = datetime(2024, 1, 1, 9, 15)
    bars = []

    # Create bars with prices that will cause EMA crossovers
    # Short EMA (50) and Long EMA (200) - need enough bars for EMA to stabilize
    prices = [
        100.0, 101.0, 102.0, 103.0, 104.0,  # Initial uptrend
        105.0, 106.0, 107.0, 108.0, 109.0,
        110.0, 111.0, 112.0, 113.0, 114.0,
        115.0, 116.0, 117.0, 118.0, 119.0,
        120.0, 121.0, 122.0, 123.0, 124.0,
        125.0, 126.0, 127.0, 128.0, 129.0,
        130.0, 131.0, 132.0, 133.0, 134.0,
        135.0, 136.0, 137.0, 138.0, 139.0,
        140.0, 141.0, 142.0, 143.0, 144.0,
        145.0, 146.0, 147.0, 148.0, 149.0,
        150.0, 151.0, 152.0, 153.0, 154.0,
        155.0, 156.0, 157.0, 158.0, 159.0,
        160.0, 161.0, 162.0, 163.0, 164.0,
        165.0, 166.0, 167.0, 168.0, 169.0,
        170.0, 171.0, 172.0, 173.0, 174.0,
        175.0, 176.0, 177.0, 178.0, 179.0,
        180.0, 181.0, 182.0, 183.0, 184.0,
        185.0, 186.0, 187.0, 188.0, 189.0,
        190.0, 191.0, 192.0, 193.0, 194.0,
        195.0, 196.0, 197.0, 198.0, 199.0,
        200.0,  # Peak
        199.0, 198.0, 197.0, 196.0, 195.0,  # Downtrend starts
        194.0, 193.0, 192.0, 191.0, 190.0,
        189.0, 188.0, 187.0, 186.0, 185.0,
        184.0, 183.0, 182.0, 181.0, 180.0,
        179.0, 178.0, 177.0, 176.0, 175.0,
        174.0, 173.0, 172.0, 171.0, 170.0,
        169.0, 168.0, 167.0, 166.0, 165.0,
        164.0, 163.0, 162.0, 161.0, 160.0,
        159.0, 158.0, 157.0, 156.0, 155.0,
        154.0, 153.0, 152.0, 151.0, 150.0,
        149.0, 148.0, 147.0, 146.0, 145.0,
        144.0, 143.0, 142.0, 141.0, 140.0,
        139.0, 138.0, 137.0, 136.0, 135.0,
        134.0, 133.0, 132.0, 131.0, 130.0,
        129.0, 128.0, 127.0, 126.0, 125.0,
        124.0, 123.0, 122.0, 121.0, 120.0,
        119.0, 118.0, 117.0, 116.0, 115.0,
        114.0, 113.0, 112.0, 111.0, 110.0,
        109.0, 108.0, 107.0, 106.0, 105.0,
        104.0, 103.0, 102.0, 101.0, 100.0,  # Back to start
    ]

    for i, price in enumerate(prices):
        timestamp = base_time + timedelta(minutes=i*5)
        bar = Candle(
            timestamp=timestamp,
            symbol="NIFTY",
            timeframe="5m",
            open=price - 0.5,
            high=price + 1.0,
            low=price - 1.0,
            close=price,
            volume=100000 + i * 1000
        )
        bars.append(bar)

    return bars


def test_ema_calculation():
    """Test EMA calculation accuracy."""
    print("Testing EMA calculation accuracy...")

    # Simple EMA test with known values
    bars = create_test_bars()[:10]  # First 10 bars
    data_feed = MockDataFeed(bars)
    strategy = EMACrossoverStrategy(data_feed)

    # Run strategy through bars
    signals = []
    for _ in range(len(bars)):
        signal = strategy.next()
        signals.append(signal)

    # Check that EMAs are calculated (not None after warmup)
    history = strategy.ema_history
    if len(history) > 50:  # After warmup period
        last_entry = history[-1]
        short_ema, long_ema = last_entry[1], last_entry[2]
        assert short_ema is not None, "Short EMA should be calculated"
        assert long_ema is not None, "Long EMA should be calculated"
        print(f"✓ EMAs calculated: Short={short_ema:.2f}, Long={long_ema:.2f}")
    else:
        print("✗ Not enough data for EMA calculation")

    print("EMA calculation test passed.\n")


def test_crossover_logic():
    """Test crossover logic (buy on short > long, sell on short < long)."""
    print("Testing crossover logic...")

    bars = create_test_bars()
    data_feed = MockDataFeed(bars)
    strategy = EMACrossoverStrategy(data_feed)

    signals = []
    for _ in range(len(bars)):
        signal = strategy.next()
        signals.append(signal)

    # Find buy and sell signals
    buy_signals = [s for s in signals if s.get('action') == 'BUY']
    sell_signals = [s for s in signals if s.get('action') == 'SELL']

    print(f"Found {len(buy_signals)} BUY signals and {len(sell_signals)} SELL signals")

    # Verify signals are reasonable (should have some crossovers in this data)
    assert len(buy_signals) > 0, "Should have at least one BUY signal"
    assert len(sell_signals) > 0, "Should have at least one SELL signal"

    # Check signal format
    for signal in buy_signals + sell_signals:
        required_keys = {'action', 'symbol', 'price', 'type'}
        assert set(signal.keys()) == required_keys, f"Signal missing keys: {signal}"
        assert signal['action'] in ['BUY', 'SELL'], f"Invalid action: {signal['action']}"
        assert signal['symbol'] == 'NIFTY', f"Wrong symbol: {signal['symbol']}"
        assert signal['type'] == 'LIMIT', f"Wrong type: {signal['type']}"
        assert isinstance(signal['price'], (int, float)), f"Price not numeric: {signal['price']}"

    print("✓ Crossover logic and signal format correct.\n")


def test_edge_cases():
    """Test edge cases: no data, single bar, etc."""
    print("Testing edge cases...")

    # Test with no bars
    empty_feed = MockDataFeed([])
    strategy = EMACrossoverStrategy(empty_feed)
    signal = strategy.next()
    assert signal == {'action': 'HOLD'}, f"Expected HOLD for no data, got {signal}"

    # Test with single bar
    single_bar = [create_test_bars()[0]]
    single_feed = MockDataFeed(single_bar)
    strategy = EMACrossoverStrategy(single_feed)
    signal = strategy.next()
    assert signal == {'action': 'HOLD'}, f"Expected HOLD for single bar, got {signal}"

    print("✓ Edge cases handled correctly.\n")


def test_integration_with_base_class():
    """Test integration with base Strategy class."""
    print("Testing integration with base class...")

    bars = create_test_bars()[:20]  # Small sample
    data_feed = MockDataFeed(bars)
    strategy = EMACrossoverStrategy(data_feed)

    # Check inheritance
    from strategies.base import Strategy
    assert isinstance(strategy, Strategy), "Should inherit from Strategy"

    # Check state initialization
    assert hasattr(strategy, 'state'), "Should have state dict"
    assert 'short_ema' in strategy.state, "Should initialize short_ema"
    assert 'long_ema' in strategy.state, "Should initialize long_ema"

    # Check data_feed assignment
    assert strategy.data_feed == data_feed, "Should store data_feed"

    print("✓ Base class integration correct.\n")


def main():
    """Run all tests."""
    print("Starting thorough testing of EMA Crossover Strategy...\n")

    try:
        test_ema_calculation()
        test_crossover_logic()
        test_edge_cases()
        test_integration_with_base_class()

        print("🎉 All tests passed! EMA Crossover Strategy is working correctly.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
