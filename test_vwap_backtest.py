#!/usr/bin/env python3
"""Backtest integration test for VWAP Microtrend Strategy."""

import sys
import pandas as pd
from datetime import datetime, timedelta

# Add strategies and backtesting to path
sys.path.append('strategies')
sys.path.append('backtesting')

from strategies.vwap_microtrend.strategy import VWAPMicrotrendStrategy
from backtesting.engine import BacktestEngine


def create_sample_data() -> pd.DataFrame:
    """Create sample 5-minute OHLCV data for testing."""
    base_time = datetime(2024, 1, 1, 9, 15)
    data = []

    # Create 2 hours of 5-minute bars (24 bars)
    for i in range(24):
        timestamp = base_time + timedelta(minutes=i*5)

        # Create trending price data with some volatility
        base_price = 100.0 + (i * 0.5)  # Upward trend
        open_price = base_price + (i % 3 - 1) * 0.2  # Some oscillation
        high = open_price + abs(i % 5 - 2) * 0.3
        low = open_price - abs(i % 4 - 1) * 0.2
        close = open_price + (i % 7 - 3) * 0.1
        volume = 100000 + (i * 5000)  # Increasing volume

        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


def test_backtest_integration():
    """Test VWAP Microtrend strategy with backtesting engine."""
    print("Testing VWAP Microtrend backtest integration...")

    # Create sample data
    df = create_sample_data()
    print(f"Created sample data with {len(df)} bars")

    # Initialize backtest engine
    engine = BacktestEngine(initial_cash=100000, commission=0.001)

    # Load data
    engine.load_data(df, 'NIFTY')

    # Add strategy
    engine.add_strategy(VWAPMicrotrendStrategy)

    # Run backtest
    print("Running backtest...")
    engine.run()

    print("✓ Backtest integration successful.\n")


def main():
    """Run backtest integration test."""
    print("Starting VWAP Microtrend backtest integration test...\n")

    try:
        test_backtest_integration()
        print("🎉 Backtest integration test passed!")
    except Exception as e:
        print(f"❌ Backtest integration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
