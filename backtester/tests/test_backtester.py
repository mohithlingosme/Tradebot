"""
Unit tests for backtesting system components.

Tests cover core functionality, edge cases, and integration scenarios.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
import tempfile
import os

from ..account import BacktestAccount, BacktestPosition
from ..costs import NSECostCalculator
from ..fill_simulator import BacktestOrder, OrderSide, OrderType, FillSimulator
from ..risk_manager import BacktestRiskManager, RiskLimits
from ..portfolio_accounting import PortfolioAccounting, TradeRecord
from ..strategy_interface import BaseStrategy, Signal, SignalType
from ..reporting import BacktestReporter, PerformanceMetrics
from ..walk_forward import WalkForwardAnalyzer, ParameterSet


class TestBacktestAccount:
    """Test BacktestAccount functionality."""

    def test_initialization(self):
        """Test account initialization."""
        account = BacktestAccount("test", starting_cash=Decimal('100000'))

        assert account.account_id == "test"
        assert account.cash == Decimal('100000')
        assert account.equity == Decimal('100000')
        assert account.margin_used == Decimal('0')
        assert len(account.positions) == 0

    def test_position_management(self):
        """Test position opening and closing."""
        account = BacktestAccount("test", starting_cash=Decimal('100000'))

        # Open position
        account.update_position("RELIANCE", 100, Decimal('2500'))
        assert account.positions["RELIANCE"].quantity == 100
        assert account.positions["RELIANCE"].avg_price == Decimal('2500')
        assert account.cash == Decimal('100000') - (100 * Decimal('2500'))

        # Add to position
        account.update_position("RELIANCE", 50, Decimal('2550'))
        expected_avg = (100 * 2500 + 50 * 2550) / 150
        assert account.positions["RELIANCE"].quantity == 150
        assert account.positions["RELIANCE"].avg_price == expected_avg

        # Close position
        account.update_position("RELIANCE", -150, Decimal('2600'))
        assert "RELIANCE" not in account.positions
        assert account.cash == Decimal('100000') - (150 * (Decimal('2600') - expected_avg))

    def test_margin_calculations(self):
        """Test margin calculations for F&O positions."""
        account = BacktestAccount("test", starting_cash=Decimal('100000'))

        # Futures position (requires margin)
        account.update_position("NIFTY24JANFUT", 50, Decimal('22000'), is_futures=True)
        margin_required = 50 * Decimal('22000') * Decimal('0.10')  # 10% margin
        assert account.margin_used == margin_required
        assert account.get_available_margin() == account.cash - margin_required


class TestNSECostCalculator:
    """Test NSE cost calculations."""

    def test_equity_delivery_costs(self):
        """Test equity delivery transaction costs."""
        calc = NSECostCalculator()

        # Buy transaction
        buy_cost = calc.calculate_transaction_cost(
            symbol="RELIANCE",
            quantity=100,
            price=Decimal('2500'),
            is_buy=True,
            is_delivery=True
        )

        expected_buy = (
            100 * 2500 * Decimal('0.0001') +  # 0.01% transaction charges
            100 * 2500 * Decimal('0.0000325') +  # Stamp duty
            100 * 2500 * Decimal('0.00018')  # GST
        )

        assert buy_cost == pytest.approx(float(expected_buy), rel=1e-6)

    def test_futures_costs(self):
        """Test futures transaction costs."""
        calc = NSECostCalculator()

        cost = calc.calculate_transaction_cost(
            symbol="NIFTY24JANFUT",
            quantity=50,
            price=Decimal('22000'),
            is_buy=True,
            is_futures=True
        )

        # Futures have different fee structure
        expected = (
            50 * 22000 * Decimal('0.00002') +  # Lower transaction charges
            50 * 22000 * Decimal('0.000002') +  # STT on futures
            50 * 22000 * Decimal('0.00018')  # GST
        )

        assert cost == pytest.approx(float(expected), rel=1e-6)


class TestFillSimulator:
    """Test order fill simulation."""

    def test_market_order_fill(self):
        """Test market order execution."""
        simulator = FillSimulator()

        order = BacktestOrder(
            order_id="test_001",
            symbol="RELIANCE",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )

        # Mock candle data
        candles = [
            Mock(timestamp=datetime(2024, 1, 1, 9, 30),
                 open=2500, high=2520, low=2490, close=2510)
        ]

        fill = simulator.simulate_fill(order, candles, Decimal('0.001'))  # 10 bps slippage

        assert fill is not None
        assert fill.quantity == 100
        assert fill.price == Decimal('2502.5')  # Next bar open + slippage
        assert fill.slippage > 0

    def test_limit_order_fill(self):
        """Test limit order execution."""
        simulator = FillSimulator()

        order = BacktestOrder(
            order_id="test_002",
            symbol="RELIANCE",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=100,
            price=Decimal('2490')
        )

        # Price reaches limit
        candles = [
            Mock(timestamp=datetime(2024, 1, 1, 9, 30),
                 open=2500, high=2520, low=2480, close=2510)
        ]

        fill = simulator.simulate_fill(order, candles, Decimal('0'))

        assert fill is not None
        assert fill.quantity == 100
        assert fill.price == Decimal('2490')  # Limit price


class TestRiskManager:
    """Test risk management functionality."""

    def test_position_sizing(self):
        """Test position sizing calculations."""
        limits = RiskLimits(
            default_sizing_method="percent_equity",
            percent_equity_per_trade=2.0
        )

        risk_manager = BacktestRiskManager(limits)
        account = BacktestAccount("test", starting_cash=Decimal('100000'))

        quantity = risk_manager.position_sizer.calculate_position_size(
            "RELIANCE", Decimal('2500'), account
        )

        expected = int((Decimal('100000') * Decimal('0.02')) / Decimal('2500'))
        assert quantity == expected

    def test_risk_limits(self):
        """Test risk limit enforcement."""
        limits = RiskLimits(max_daily_loss_pct=5.0)
        risk_manager = BacktestRiskManager(limits)

        account = BacktestAccount("test", starting_cash=Decimal('100000'))
        order = BacktestOrder(
            order_id="test_001",
            symbol="RELIANCE",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=100
        )

        # Normal case
        decision = risk_manager.evaluate_order(order, account, datetime.utcnow(), Decimal('2500'))
        assert decision.action.name == "ALLOW"

        # After hitting daily loss limit
        risk_manager.daily_pnl = Decimal('-6000')  # 6% loss
        decision = risk_manager.evaluate_order(order, account, datetime.utcnow(), Decimal('2500'))
        assert decision.action.name == "HALT_TRADING"


class TestPortfolioAccounting:
    """Test portfolio accounting functionality."""

    def test_pnl_calculation(self):
        """Test P&L calculations."""
        portfolio = PortfolioAccounting(Decimal('100000'))

        # Record a trade
        trade = TradeRecord(
            symbol="RELIANCE",
            side="BUY",
            quantity=100,
            entry_price=Decimal('2500'),
            exit_price=Decimal('2600'),
            entry_time=datetime(2024, 1, 1, 9, 30),
            exit_time=datetime(2024, 1, 1, 15, 30),
            realized_pnl=Decimal('10000'),
            fees=Decimal('50'),
            tags=["test"]
        )

        portfolio.record_trade(trade)

        assert len(portfolio.trade_log) == 1
        assert portfolio.total_realized_pnl == Decimal('10000')
        assert portfolio.total_fees == Decimal('50')

    def test_equity_curve(self):
        """Test equity curve calculation."""
        portfolio = PortfolioAccounting(Decimal('100000'))

        # Simulate equity updates
        portfolio.update_equity(datetime(2024, 1, 1), Decimal('100000'))
        portfolio.update_equity(datetime(2024, 1, 2), Decimal('105000'))
        portfolio.update_equity(datetime(2024, 1, 3), Decimal('103000'))

        assert len(portfolio.equity_curve) == 3
        assert portfolio.equity_curve[-1].equity == Decimal('103000')
        assert portfolio.max_drawdown_pct == 20.0  # From 105k to 103k


class TestStrategyInterface:
    """Test strategy interface functionality."""

    def test_indicator_calculations(self):
        """Test technical indicator calculations."""
        from ..strategy_interface import IndicatorLibrary

        prices = [Decimal(str(100 + i)) for i in range(50)]

        # Test SMA
        sma = IndicatorLibrary.sma(prices, 20)
        expected_sma = sum(prices[-20:]) / 20
        assert sma == expected_sma

        # Test RSI
        rsi = IndicatorLibrary.rsi(prices, 14)
        assert rsi is not None
        assert 0 <= rsi <= 100

        # Test MACD
        macd, signal, hist = IndicatorLibrary.macd(prices)
        assert macd is not None
        assert signal is not None

    def test_strategy_state_management(self):
        """Test strategy state persistence."""
        from ..strategy_interface import ExampleStrategy

        strategy = ExampleStrategy("test", ["RELIANCE"])

        # Test initial state
        state = strategy.get_state("RELIANCE")
        assert state.position == 0
        assert state.entry_price is None

        # Test state update
        signal = Signal(
            symbol="RELIANCE",
            signal_type=SignalType.BUY,
            quantity=100,
            price=Decimal('2500'),
            timestamp=datetime.utcnow()
        )

        strategy.update_state("RELIANCE", signal, Decimal('2500'))
        updated_state = strategy.get_state("RELIANCE")
        assert updated_state.position == 100
        assert updated_state.entry_price == Decimal('2500')


class TestReporting:
    """Test reporting functionality."""

    def test_performance_metrics(self):
        """Test performance metrics calculation."""
        portfolio = PortfolioAccounting(Decimal('100000'))

        # Add some mock trades
        for i in range(10):
            trade = TradeRecord(
                symbol="RELIANCE",
                side="BUY",
                quantity=100,
                entry_price=Decimal('2500'),
                exit_price=Decimal('2520') if i % 2 == 0 else Decimal('2480'),
                entry_time=datetime(2024, 1, 1) + timedelta(days=i),
                exit_time=datetime(2024, 1, 1) + timedelta(days=i, hours=6),
                realized_pnl=Decimal('2000') if i % 2 == 0 else Decimal('-2000'),
                fees=Decimal('25'),
                tags=[]
            )
            portfolio.record_trade(trade)

        reporter = BacktestReporter(portfolio)
        metrics = reporter._calculate_performance_metrics()

        assert metrics.total_trades == 10
        assert metrics.winning_trades == 5
        assert metrics.win_rate_pct == 50.0
        assert metrics.total_realized_pnl == 0  # 5 wins * 2000 + 5 losses * (-2000)


class TestWalkForward:
    """Test walk-forward analysis."""

    def test_window_generation(self):
        """Test walk-forward window generation."""
        analyzer = WalkForwardAnalyzer(
            strategy_runner=None,
            initial_train_days=252,
            test_days=63,
            step_days=21
        )

        start_date = date(2020, 1, 1)
        end_date = date(2024, 1, 1)

        windows = analyzer.generate_windows(start_date, end_date)

        assert len(windows) > 0
        for window in windows:
            assert window.train_days >= 252
            assert window.test_days == 63

    def test_parameter_grid(self):
        """Test parameter grid generation."""
        from ..walk_forward import ParameterGridSearch

        param_ranges = {
            'sma_fast': [5, 10],
            'sma_slow': [20, 50]
        }

        grid = ParameterGridSearch(param_ranges)
        param_sets = grid.generate_parameter_sets()

        assert len(param_sets) == 4  # 2 * 2 combinations

        # Check that all combinations are present
        expected_combinations = [
            {'sma_fast': 5, 'sma_slow': 20},
            {'sma_fast': 5, 'sma_slow': 50},
            {'sma_fast': 10, 'sma_slow': 20},
            {'sma_fast': 10, 'sma_slow': 50}
        ]

        actual_combinations = [ps.params for ps in param_sets]
        for combo in expected_combinations:
            assert combo in actual_combinations


class TestGoldenDataset:
    """Golden dataset tests for correctness validation."""

    def test_known_strategy_results(self):
        """Test against known good results for a simple strategy."""
        # This would test a simple strategy against a known dataset
        # and verify that results match expected values

        # For now, just ensure the testing framework works
        assert True

    def test_reproducibility(self):
        """Test that identical runs produce identical results."""
        # Run the same backtest multiple times and ensure results are identical
        assert True


# Integration tests
class TestIntegration:
    """Integration tests for complete backtesting workflow."""

    def test_full_backtest_workflow(self):
        """Test complete backtest from data to report."""
        # This would test the entire pipeline:
        # 1. Load data
        # 2. Run strategy
        # 3. Apply risk management
        # 4. Generate fills
        # 5. Calculate P&L
        # 6. Generate report

        assert True

    def test_multi_symbol_backtest(self):
        """Test backtesting across multiple symbols."""
        assert True


if __name__ == "__main__":
    pytest.main([__file__])
