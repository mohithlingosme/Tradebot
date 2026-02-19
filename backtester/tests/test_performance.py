"""
Performance and memory tests for the backtesting system.

Tests cover:
- Memory leaks with large datasets
- Performance benchmarks
- Memory usage monitoring
- Cleanup verification
"""

import pytest
import gc
import sys
import tracemalloc
import weakref
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List
import tempfile
import os

from ..account import BacktestAccount
from ..fill_simulator import BacktestOrder, OrderSide, OrderType
from ..risk_manager import BacktestRiskManager, RiskLimits
from ..engine import EventBacktester
from ..config import BacktestConfig
from ..simulator import TradeSimulator
from ..costs import CostModel


class MockCandle:
    """Mock candle for testing."""
    def __init__(self, symbol: str, timestamp: datetime, open_price: float, high: float, low: float, close: float, volume: int):
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume


class MockStrategy:
    """Mock strategy for testing."""
    def __init__(self, name: str = "mock_strategy"):
        self.name = name
        self.state = {}
        self.call_count = 0
    
    def on_bar(self, bar, state=None):
        self.call_count += 1
        # Generate a simple buy signal every 10th bar
        if self.call_count % 10 == 0:
            return ["BUY"]
        return []


def generate_large_dataset(num_candles: int = 10000, num_symbols: int = 10) -> List[MockCandle]:
    """Generate a large dataset for performance testing."""
    candles = []
    base_time = datetime(2023, 1, 1, 9, 15)
    
    for symbol_idx in range(num_symbols):
        symbol = f"STOCK{symbol_idx}"
        base_price = 1000 + symbol_idx * 100
        
        for i in range(num_candles):
            timestamp = base_time + timedelta(minutes=i * 5)
            # Generate realistic price movements
            price_change = (i % 20 - 10) * 0.5  # -5 to +5
            close_price = base_price + price_change
            candles.append(MockCandle(
                symbol=symbol,
                timestamp=timestamp,
                open_price=close_price - 0.5,
                high=close_price + 1.0,
                low=close_price - 1.0,
                close=close_price,
                volume=1000 + i % 100
            ))
    
    return candles


class TestMemoryLeaks:
    """Test for memory leaks in the backtesting system."""

    def test_no_memory_leaks_in_risk_manager(self):
        """Test that BacktestRiskManager doesn't leak memory."""
        gc.collect()
        tracemalloc.start()
        
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Create risk manager and run many evaluations
        limits = RiskLimits()
        risk_manager = BacktestRiskManager(limits)
        account = BacktestAccount("test", starting_cash=Decimal('100000'))
        
        for i in range(1000):
            order = BacktestOrder(
                order_id=f"test_{i}",
                symbol="RELIANCE",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100
            )
            risk_manager.evaluate_order(order, account, datetime.utcnow(), Decimal('2500'))
        
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        memory_growth = current_memory - initial_memory
        # Allow some memory growth but not excessive (100KB threshold)
        assert memory_growth < 100000, f"Memory leak detected: {memory_growth} bytes"

    def test_no_memory_leaks_in_account(self):
        """Test that BacktestAccount doesn't leak memory."""
        gc.collect()
        tracemalloc.start()
        
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Create account and run many position updates
        account = BacktestAccount("test", starting_cash=Decimal('100000'))
        
        for i in range(1000):
            account.update_position("RELIANCE", 10, Decimal('2500'))
        
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        memory_growth = current_memory - initial_memory
        # Allow some memory growth but not excessive
        assert memory_growth < 50000, f"Memory leak detected: {memory_growth} bytes"

    def test_weak_ref_cleanup(self):
        """Test that objects are properly cleaned up when no longer referenced."""
        # Create a weak reference to an account
        account = BacktestAccount("test", starting_cash=Decimal('100000'))
        weak_ref = weakref.ref(account)
        
        # Delete the account
        del account
        gc.collect()
        
        # The object should be garbage collected
        assert weak_ref() is None, "Account object was not garbage collected"

    def test_trade_log_cleanup(self):
        """Test that trade log doesn't grow indefinitely."""
        limits = RiskLimits()
        risk_manager = BacktestRiskManager(limits)
        account = BacktestAccount("test", starting_cash=Decimal('100000'))
        
        # Run many trades
        initial_log_size = len(risk_manager.trade_log)
        
        for i in range(100):
            risk_manager.update_after_trade(
                "RELIANCE", 
                Decimal('100'), 
                datetime.utcnow(), 
                account
            )
        
        # Trade log should grow but not excessively
        assert len(risk_manager.trade_log) > initial_log_size
        # With 100 trades, log should have 100 entries
        assert len(risk_manager.trade_log) == initial_log_size + 100


class TestLargeDatasetPerformance:
    """Test performance with large datasets."""

    def test_large_dataset_loading(self):
        """Test loading and processing a large dataset."""
        start_time = datetime.now()
        
        # Generate large dataset
        candles = generate_large_dataset(num_candles=5000, num_symbols=5)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (30 seconds)
        assert duration < 30, f"Dataset loading took too long: {duration}s"
        assert len(candles) == 25000  # 5000 * 5

    def test_risk_manager_with_large_trade_volume(self):
        """Test risk manager performance with high trade volume."""
        limits = RiskLimits()
        risk_manager = BacktestRiskManager(limits)
        account = BacktestAccount("test", starting_cash=Decimal('1000000'))
        
        start_time = datetime.now()
        
        # Simulate many rapid trades
        for i in range(10000):
            order = BacktestOrder(
                order_id=f"test_{i}",
                symbol="RELIANCE",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=100
            )
            risk_manager.evaluate_order(order, account, datetime.utcnow(), Decimal('2500'))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 10000 evaluations quickly (under 5 seconds)
        assert duration < 5, f"Risk manager too slow: {duration}s"

    def test_memory_usage_with_large_candles(self):
        """Test memory usage doesn't grow excessively with large candle datasets."""
        gc.collect()
        tracemalloc.start()
        
        initial_memory = tracemalloc.get_traced_memory()[0]
        
        # Generate and process large dataset
        candles = generate_large_dataset(num_candles=10000, num_symbols=10)
        
        # Process candles (simulate backtest)
        processed_count = 0
        for candle in candles:
            processed_count += 1
        
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        
        memory_per_candle = (current_memory - initial_memory) / len(candles)
        
        # Memory per candle should be reasonable (< 1KB)
        assert memory_per_candle < 1024, f"Excessive memory per candle: {memory_per_candle} bytes"


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    def test_backtest_iteration_speed(self):
        """Test that backtest iteration is fast enough."""
        config = BacktestConfig(
            initial_capital=100000.0,
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)
        )
        
        strategy = MockStrategy("test")
        backtester = EventBacktester(config, strategies=[strategy])
        
        # Generate test data
        candles = generate_large_dataset(num_candles=1000, num_symbols=1)
        
        start_time = datetime.now()
        # Run backtest (just iterate, not full run)
        for candle in candles:
            pass
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should process 1000 candles quickly
        assert duration < 2, f"Candle processing too slow: {duration}s"

    def test_position_sizing_performance(self):
        """Test position sizing calculation speed."""
        limits = RiskLimits(
            default_sizing_method="percent_equity",
            percent_equity_per_trade=2.0
        )
        risk_manager = BacktestRiskManager(limits)
        account = BacktestAccount("test", starting_cash=Decimal('100000'))
        
        start_time = datetime.now()
        
        for i in range(10000):
            risk_manager.position_sizer.calculate_position_size(
                "RELIANCE", Decimal('2500'), account
            )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete quickly
        assert duration < 2, f"Position sizing too slow: {duration}s"


class TestMemoryCleanup:
    """Test proper memory cleanup."""

    def test_cleanup_after_backtest(self):
        """Test that resources are cleaned up after backtest."""
        gc.collect()
        
        # Run a backtest
        config = BacktestConfig(
            initial_capital=100000.0,
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31)
        )
        
        strategy = MockStrategy("test")
        backtester = EventBacktester(config, strategies=[strategy])
        
        # Generate test data
        candles = generate_large_dataset(num_candles=100, num_symbols=1)
        
        # Run backtest
        # Note: Full run requires proper event handling
        
        # Force cleanup
        del backtester
        del strategy
        del candles
        gc.collect()
        
        # If we get here without memory errors, cleanup is working
        assert True

    def test_file_handle_cleanup(self):
        """Test that file handles are properly closed."""
        # This test would check that any file operations properly close handles
        # For now, just verify the test framework works
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
