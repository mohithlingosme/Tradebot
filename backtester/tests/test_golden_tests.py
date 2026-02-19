"""
Golden tests for backtesting consistency validation.

Tests cover:
- Running golden tests against reference artifacts
- Generating reference artifacts
- Verifying equity curve consistency
- Verifying trade log consistency
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List

from ..golden_test import GoldenTestTemplate, GoldenTestResult
from ..reporting import BacktestReport, PerformanceMetrics, PortfolioAccounting
from ..portfolio_accounting import TradeRecord


class MockEquityPoint:
    """Mock equity point for testing."""
    def __init__(self, timestamp: datetime, equity: float):
        self.timestamp = timestamp
        self.equity = Decimal(str(equity))


class MockTrade:
    """Mock trade for testing."""
    def __init__(self, symbol: str, side: str, quantity: float, 
                 entry_price: float, exit_price: float,
                 entry_time: datetime, exit_time: datetime,
                 realized_pnl: float, fees: float = 0.0):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.realized_pnl = realized_pnl
        self.fees = fees


class MockPortfolioAccounting:
    """Mock portfolio accounting for testing."""
    def __init__(self):
        self.equity_curve: List[MockEquityPoint] = []
        self.trade_log: List[MockTrade] = []


class MockReport:
    """Mock backtest report for testing."""
    def __init__(self, equity_curve: List[MockEquityPoint], trade_log: List[MockTrade]):
        self.portfolio_accounting = MockPortfolioAccounting()
        self.portfolio_accounting.equity_curve = equity_curve
        self.portfolio_accounting.trade_log = trade_log
        self.strategy_name = "test_strategy"
        self.symbols = ["RELIANCE"]
        self.start_date = date(2023, 1, 1)
        self.end_date = date(2023, 12, 31)
        self.initial_capital = 100000.0
        self.parameters = {}


def create_sample_report() -> MockReport:
    """Create a sample report for testing."""
    equity_curve = []
    trade_log = []
    
    base_time = datetime(2023, 1, 1, 9, 30)
    equity = 100000.0
    
    # Create equity curve points
    for i in range(100):
        timestamp = base_time + timedelta(days=i)
        equity += (i % 10 - 5) * 100  # Fluctuate equity
        equity_curve.append(MockEquityPoint(timestamp, equity))
    
    # Create some trades
    for i in range(10):
        entry_time = base_time + timedelta(days=i * 10)
        exit_time = entry_time + timedelta(days=5)
        trade_log.append(MockTrade(
            symbol="RELIANCE",
            side="BUY",
            quantity=100.0,
            entry_price=2500.0,
            exit_price=2520.0,
            entry_time=entry_time,
            exit_time=exit_time,
            realized_pnl=2000.0,
            fees=50.0
        ))
    
    return MockReport(equity_curve, trade_log)


class TestGoldenTestTemplate:
    """Test GoldenTestTemplate functionality."""

    def test_create_reference_artifacts(self):
        """Test creating reference artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            report = create_sample_report()
            
            # Create reference artifacts
            template.create_reference_artifacts(report, "test_golden")
            
            # Verify files were created
            test_dir = Path(tmpdir) / "test_golden"
            assert (test_dir / "equity_curve.json").exists()
            assert (test_dir / "trade_log.json").exists()
            assert (test_dir / "metadata.json").exists()

    def test_run_golden_test_identical(self):
        """Test running golden test with identical data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            report = create_sample_report()
            
            # Create reference artifacts
            template.create_reference_artifacts(report, "test_golden")
            
            # Run golden test with identical report
            result = template.run_golden_test(report, "test_golden")
            
            assert result.passed == True
            assert result.equity_curve_diff < template.tolerance
            assert result.trade_log_diff == 0

    def test_run_golden_test_slightly_different(self):
        """Test running golden test with slightly different data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            
            # Create reference report
            ref_report = create_sample_report()
            template.create_reference_artifacts(ref_report, "test_golden")
            
            # Create slightly different report
            different_report = create_sample_report()
            # Modify one equity point slightly
            different_report.portfolio_accounting.equity_curve[50].equity += Decimal('10')
            
            # Run golden test
            result = template.run_golden_test(different_report, "test_golden")
            
            # Should fail due to difference
            assert result.passed == False

    def test_equity_curve_comparison(self):
        """Test equity curve comparison."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            
            # Create reference
            ref_equity = {
                "timestamps": [datetime(2023, 1, 1).isoformat()],
                "equity_values": [100000.0]
            }
            
            # Test identical curves
            current_curve = [MockEquityPoint(datetime(2023, 1, 1), 100000.0)]
            diff, max_dev = template._compare_equity_curves(current_curve, ref_equity)
            
            assert diff == 0.0
            assert max_dev == 0.0

    def test_trade_log_comparison(self):
        """Test trade log comparison."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            
            # Create reference trades
            ref_trades = [{
                "symbol": "RELIANCE",
                "side": "BUY",
                "quantity": 100.0,
                "entry_price": 2500.0,
                "exit_price": 2520.0,
                "realized_pnl": 2000.0
            }]
            
            # Test identical trades
            current_trades = [MockTrade(
                symbol="RELIANCE",
                side="BUY",
                quantity=100.0,
                entry_price=2500.0,
                exit_price=2520.0,
                entry_time=datetime(2023, 1, 1),
                exit_time=datetime(2023, 1, 5),
                realized_pnl=2000.0,
                fees=50.0
            )]
            
            diff, max_dev = template._compare_trade_logs(current_trades, ref_trades)
            
            assert diff == 0
            # Should be very close (within tolerance)
            assert max_dev < 0.001


class TestGoldenTestConsistency:
    """Test golden test consistency across runs."""

    def test_reproducibility(self):
        """Test that identical runs produce identical results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            
            # Create initial reference
            report1 = create_sample_report()
            template.create_reference_artifacts(report1, "reproducibility_test")
            
            # Run golden test
            result1 = template.run_golden_test(report1, "reproducibility_test")
            
            # Run again
            result2 = template.run_golden_test(report1, "reproducibility_test")
            
            # Results should be identical
            assert result1.passed == result2.passed
            assert result1.equity_curve_diff == result2.equity_curve_diff

    def test_tolerance_threshold(self):
        """Test tolerance threshold for floating point comparisons."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir, tolerance=0.0001)
            
            # Create reference with 100000.0
            ref_equity = {
                "timestamps": [datetime(2023, 1, 1).isoformat()],
                "equity_values": [100000.0]
            }
            
            # Test with small difference (0.001%)
            current_curve = [MockEquityPoint(datetime(2023, 1, 1), 100000.1)]
            diff, max_dev = template._compare_equity_curves(current_curve, ref_equity)
            
            # Should pass (within 0.01% tolerance)
            assert diff < template.tolerance

    def test_fails_different_trade_count(self):
        """Test that different trade counts are detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            
            # Reference with 10 trades
            ref_trades = [
                {"symbol": "RELIANCE", "side": "BUY", "quantity": 100.0, 
                 "entry_price": 2500.0, "exit_price": 2520.0, "realized_pnl": 2000.0}
                for _ in range(10)
            ]
            
            # Current with 11 trades
            current_trades = [MockTrade(
                symbol="RELIANCE", side="BUY", quantity=100.0,
                entry_price=2500.0, exit_price=2520.0,
                entry_time=datetime(2023, 1, 1), exit_time=datetime(2023, 1, 5),
                realized_pnl=2000.0, fees=50.0
            ) for _ in range(11)]
            
            diff, _ = template._compare_trade_logs(current_trades, ref_trades)
            
            # Should detect difference
            assert diff > 0


class TestGoldenTestErrorHandling:
    """Test error handling in golden tests."""

    def test_missing_reference_raises_error(self):
        """Test that missing reference raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            report = create_sample_report()
            
            with pytest.raises(FileNotFoundError):
                template.run_golden_test(report, "nonexistent_test")

    def test_missing_equity_file_raises_error(self):
        """Test that missing equity file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            report = create_sample_report()
            
            # Create reference directory but not files
            test_dir = Path(tmpdir) / "test_golden"
            test_dir.mkdir()
            
            with pytest.raises(FileNotFoundError):
                template.run_golden_test(report, "test_golden")


class TestGoldenTestIntegration:
    """Integration tests for golden tests."""

    def test_full_golden_test_workflow(self):
        """Test complete golden test workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = GoldenTestTemplate(reference_dir=tmpdir)
            
            # Step 1: Create initial reference
            initial_report = create_sample_report()
            template.create_reference_artifacts(initial_report, "integration_test")
            
            # Step 2: Run golden test with same data (should pass)
            result = template.run_golden_test(initial_report, "integration_test")
            assert result.passed == True
            
            # Step 3: Verify result details
            assert result.test_name == "integration_test"
            assert result.details["equity_curve_length"] == 100
            assert result.details["trade_log_length"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
