"""
Golden Test for Backtesting Regression Testing

This module implements golden tests that ensure backtest results remain
consistent across code changes. It runs a strategy on a fixed dataset and
compares the equity curve and trade logs against stored reference artifacts.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import pandas as pd

from .reporting import BacktestReport
from .engine import EventBacktester
from .config import BacktestConfig
from .strategy_interface import create_strategy


@dataclass
class GoldenTestResult:
    """Result of a golden test comparison."""
    test_name: str
    passed: bool
    equity_curve_diff: float
    trade_log_diff: int
    max_equity_deviation: float
    max_trade_deviation: float
    details: Dict[str, Any]


class GoldenTestTemplate:
    """
    Template for creating golden tests that compare backtest results
    against reference artifacts.

    Usage:
    1. Run a backtest with known parameters on a fixed dataset
    2. Save the results as reference artifacts
    3. Create a test that runs the same backtest and compares results
    """

    def __init__(self, reference_dir: str = "golden_tests/reference"):
        self.reference_dir = Path(reference_dir)
        self.reference_dir.mkdir(parents=True, exist_ok=True)
        self.tolerance = 0.0001  # 0.01% tolerance for equity values

    def create_reference_artifacts(self, report: BacktestReport, test_name: str) -> None:
        """
        Create reference artifacts from a backtest report.

        This should be run once to establish the baseline for regression testing.
        """
        test_dir = self.reference_dir / test_name
        test_dir.mkdir(exist_ok=True)

        # Save equity curve
        equity_data = {
            "timestamps": [point.timestamp.isoformat() for point in report.portfolio_accounting.equity_curve],
            "equity_values": [float(point.equity) for point in report.portfolio_accounting.equity_curve]
        }

        with open(test_dir / "equity_curve.json", 'w') as f:
            json.dump(equity_data, f, indent=2)

        # Save trade log
        trade_data = []
        for trade in report.portfolio_accounting.trade_log:
            trade_data.append({
                "symbol": trade.symbol,
                "side": trade.side,
                "quantity": float(trade.quantity),
                "entry_price": float(trade.entry_price),
                "exit_price": float(trade.exit_price),
                "entry_time": trade.entry_time.isoformat(),
                "exit_time": trade.exit_time.isoformat(),
                "realized_pnl": float(trade.realized_pnl),
                "fees": float(trade.fees)
            })

        with open(test_dir / "trade_log.json", 'w') as f:
            json.dump(trade_data, f, indent=2)

        # Save metadata
        metadata = {
            "test_name": test_name,
            "created_at": datetime.utcnow().isoformat(),
            "strategy_name": report.strategy_name,
            "symbols": report.symbols,
            "start_date": report.start_date.isoformat(),
            "end_date": report.end_date.isoformat(),
            "initial_capital": report.initial_capital,
            "parameters": getattr(report, 'parameters', {})
        }

        with open(test_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Reference artifacts created for test: {test_name}")

    def run_golden_test(self, report: BacktestReport, test_name: str) -> GoldenTestResult:
        """
        Run a golden test by comparing the report against reference artifacts.
        """
        test_dir = self.reference_dir / test_name

        if not test_dir.exists():
            raise FileNotFoundError(f"Reference artifacts not found for test: {test_name}")

        # Load reference data
        with open(test_dir / "equity_curve.json", 'r') as f:
            ref_equity = json.load(f)

        with open(test_dir / "trade_log.json", 'r') as f:
            ref_trades = json.load(f)

        # Compare equity curves
        equity_diff, max_equity_deviation = self._compare_equity_curves(
            report.portfolio_accounting.equity_curve, ref_equity
        )

        # Compare trade logs
        trade_diff, max_trade_deviation = self._compare_trade_logs(
            report.portfolio_accounting.trade_log, ref_trades
        )

        # Determine pass/fail
        passed = (equity_diff <= self.tolerance and trade_diff == 0)

        result = GoldenTestResult(
            test_name=test_name,
            passed=passed,
            equity_curve_diff=equity_diff,
            trade_log_diff=trade_diff,
            max_equity_deviation=max_equity_deviation,
            max_trade_deviation=max_trade_deviation,
            details={
                "equity_curve_length": len(report.portfolio_accounting.equity_curve),
                "reference_equity_length": len(ref_equity["equity_values"]),
                "trade_log_length": len(report.portfolio_accounting.trade_log),
                "reference_trade_length": len(ref_trades)
            }
        )

        return result

    def _compare_equity_curves(self, current_curve: List, reference_data: Dict) -> Tuple[float, float]:
        """
        Compare equity curves and return (average_diff, max_deviation).
        """
        if len(current_curve) != len(reference_data["equity_values"]):
            return float('inf'), float('inf')

        diffs = []
        for i, point in enumerate(current_curve):
            ref_value = reference_data["equity_values"][i]
            current_value = float(point.equity)
            diff = abs(current_value - ref_value) / ref_value if ref_value != 0 else abs(current_value)
            diffs.append(diff)

        return sum(diffs) / len(diffs), max(diffs)

    def _compare_trade_logs(self, current_trades: List, reference_trades: List) -> Tuple[int, float]:
        """
        Compare trade logs and return (count_difference, max_deviation).
        """
        if len(current_trades) != len(reference_trades):
            return abs(len(current_trades) - len(reference_trades)), float('inf')

        max_deviation = 0.0
        for i, (current, ref) in enumerate(zip(current_trades, reference_trades)):
            # Compare key fields
            fields_to_check = ['symbol', 'side', 'quantity', 'entry_price', 'exit_price', 'realized_pnl']

            for field in fields_to_check:
                current_val = getattr(current, field, None)
                ref_val = ref.get(field)

                if current_val is None or ref_val is None:
                    continue

                # Convert to float for comparison
                try:
                    current_float = float(current_val)
                    ref_float = float(ref_val)
                    deviation = abs(current_float - ref_float) / abs(ref_float) if ref_float != 0 else abs(current_float)
                    max_deviation = max(max_deviation, deviation)
                except (ValueError, TypeError):
                    # For non-numeric fields, check exact equality
                    if str(current_val) != str(ref_val):
                        max_deviation = float('inf')

        return 0, max_deviation


# Example usage and test template
def example_golden_test():
    """
    Example of how to use the golden test template.

    This function demonstrates:
    1. Creating reference artifacts (run once)
    2. Running regression tests (run on code changes)
    """

    # Initialize the template
    golden_test = GoldenTestTemplate()

    # Example: Create reference artifacts (run this once to establish baseline)
    def create_reference():
        # This would be your actual backtest logic
        from .cli import BacktestCLI
        from datetime import date

        cli = BacktestCLI()
        report = cli._run_single_backtest(
            strategy_name="example_strategy",
            parameters={"param1": 10, "param2": 0.02},
            symbols=["RELIANCE"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

        golden_test.create_reference_artifacts(report, "example_test_2023")

    # Example: Run regression test (run this on code changes)
    def run_regression_test():
        # Run the same backtest
        from .cli import BacktestCLI
        from datetime import date

        cli = BacktestCLI()
        report = cli._run_single_backtest(
            strategy_name="example_strategy",
            parameters={"param1": 10, "param2": 0.02},
            symbols=["RELIANCE"],
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

        # Compare against reference
        result = golden_test.run_golden_test(report, "example_test_2023")

        if result.passed:
            print(f"✓ Golden test '{result.test_name}' PASSED")
        else:
            print(f"✗ Golden test '{result.test_name}' FAILED")
            print(f"  Equity curve diff: {result.equity_curve_diff:.6f}")
            print(f"  Trade log diff: {result.trade_log_diff}")
            print(f"  Max equity deviation: {result.max_equity_deviation:.6f}")
            print(f"  Max trade deviation: {result.max_trade_deviation:.6f}")

        return result

    # Uncomment to create reference or run test
    # create_reference()
    # result = run_regression_test()

    return golden_test


if __name__ == "__main__":
    # Run example
    golden_test = example_golden_test()
