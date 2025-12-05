"""
Unit tests for Trading Engine components
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
from tests.utils.paths import BACKEND_ROOT

sys.path.insert(0, str(BACKEND_ROOT))

from trading_engine.strategy_manager import StrategyManager, BaseStrategy
from trading_engine.strategies.adaptive_rsi_macd_strategy import AdaptiveRSIMACDStrategy
from trading_engine.backtester import Backtester, BacktestConfig, BacktestMode
from risk_management.portfolio_manager import PortfolioManager
from monitoring.logger import StructuredLogger, LogLevel, Component

class MockStrategy(BaseStrategy):
    """Mock strategy for testing"""

    def analyze(self, data):
        # Simple mock strategy that generates buy signals
        return {
            'signal': 'buy',
            'confidence': 0.8,
            'indicators': {'rsi': 30, 'macd': {'crossover': 'bullish'}},
            'analysis': 'Mock analysis'
        }

class TestStrategyManager(unittest.TestCase):

    def setUp(self):
        self.manager = StrategyManager()

    def test_load_strategy(self):
        """Test loading a strategy"""
        config = {'name': 'test_strategy'}
        success = self.manager.load_strategy('test', MockStrategy, config)
        self.assertTrue(success)
        self.assertIn('test', self.manager.get_available_strategies())

    def test_execute_strategy(self):
        """Test executing a strategy"""
        config = {'name': 'test_strategy'}
        self.manager.load_strategy('test', MockStrategy, config)

        data = {'close': 100, 'open': 99, 'high': 101, 'low': 98}
        result = self.manager.execute_strategy('test', data)

        self.assertIsNotNone(result)
        self.assertEqual(result['signal'], 'buy')
        self.assertEqual(result['confidence'], 0.8)

    def test_activate_deactivate_strategy(self):
        """Test activating and deactivating strategies"""
        config = {'name': 'test_strategy'}
        self.manager.load_strategy('test', MockStrategy, config)

        success = self.manager.activate_strategy('test')
        self.assertTrue(success)
        self.assertIn('test', self.manager.get_active_strategies())

        success = self.manager.deactivate_strategy('test')
        self.assertTrue(success)
        self.assertNotIn('test', self.manager.get_active_strategies())

class TestAdaptiveRSIMACDStrategy(unittest.TestCase):

    def setUp(self):
        config = {
            'name': 'adaptive_rsi_macd',
            'strategy_params': {
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9
            }
        }
        self.strategy = AdaptiveRSIMACDStrategy(config)

    def test_initialization(self):
        """Test strategy initialization"""
        self.assertEqual(self.strategy.name, 'adaptive_rsi_macd')
        self.assertIsNotNone(self.strategy.strategy_config)

    def test_rsi_calculation(self):
        """Test RSI calculation"""
        # Create test data with known RSI
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 105, 107, 106, 108]
        for price in prices:
            self.strategy._update_historical_data({'close': price})

        rsi = self.strategy._calculate_rsi(np.array(prices))
        self.assertIsInstance(rsi, float)
        self.assertTrue(0 <= rsi <= 100)

    def test_signal_generation(self):
        """Test signal generation"""
        # Create oversold condition
        data = {
            'timestamp': datetime.now(),
            'open': 95,
            'high': 105,
            'low': 95,
            'close': 98,
            'volume': 1000
        }

        result = self.strategy.analyze(data)
        self.assertIn('signal', result)
        self.assertIn('confidence', result)
        self.assertIn(result['signal'], ['buy', 'sell', 'hold', 'exit_long', 'exit_short'])

class TestPortfolioManager(unittest.TestCase):

    def setUp(self):
        config = {
            'initial_cash': 100000,
            'max_drawdown': 0.15,
            'max_daily_loss': 0.05,
            'max_position_size': 0.10
        }
        self.pm = PortfolioManager(config)

    def test_initialization(self):
        """Test portfolio manager initialization"""
        self.assertEqual(self.pm.cash, 100000)
        self.assertEqual(len(self.pm.positions), 0)

    def test_update_position(self):
        """Test position updates"""
        success = self.pm.update_position('AAPL', 100, 150.0, 'buy')
        self.assertTrue(success)
        self.assertEqual(self.pm.cash, 85000)  # 100000 - (100 * 150)

        # Check position
        self.assertIn('AAPL', self.pm.positions)
        pos = self.pm.positions['AAPL']
        self.assertEqual(pos.quantity, 100)
        self.assertEqual(pos.average_price, 150.0)

    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation"""
        initial_value = self.pm.calculate_portfolio_value()
        self.assertEqual(initial_value, 100000)

        # Add position
        self.pm.update_position('AAPL', 100, 150.0, 'buy')
        new_value = self.pm.calculate_portfolio_value()
        self.assertEqual(new_value, 100000)  # Cash + position value

    def test_risk_limits(self):
        """Test risk limit checking"""
        # Initially should pass
        status = self.pm.check_risk_limits()
        self.assertTrue(status['overall_status'])

        # Add large position that exceeds limit
        self.pm.update_position('AAPL', 1000, 150.0, 'buy')  # 150k position
        status = self.pm.check_risk_limits()
        self.assertFalse(status['overall_status'])

class TestBacktester(unittest.TestCase):

    def setUp(self):
        config = BacktestConfig(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            initial_capital=100000.0
        )
        self.backtester = Backtester(config)

    def test_initialization(self):
        """Test backtester initialization"""
        self.assertIsNotNone(self.backtester.config)
        self.assertIsNotNone(self.backtester.portfolio_manager)

    @patch('trading_engine.backtester.Backtester._execute_trade')
    def test_run_backtest(self, mock_execute):
        """Test running a backtest"""
        mock_execute.return_value = Mock(pnl=1000, quantity=10, price=100, commission=10)

        # Create mock market data
        dates = pd.date_range('2023-01-01', '2023-01-05')
        data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [105, 106, 107, 108, 109],
            'low': [95, 96, 97, 98, 99],
            'close': [102, 103, 104, 105, 106],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=dates)

        strategy = MockStrategy({'name': 'test'})
        result = self.backtester.run_backtest(strategy, data)

        self.assertIsNotNone(result)
        self.assertIsInstance(result.total_trades, int)
        self.assertIsInstance(result.total_return, float)

class TestLiveTradingEngine(unittest.TestCase):

    def setUp(self):
        from trading_engine import LiveTradingConfig, TradingMode, LiveTradingEngine

        self.config = LiveTradingConfig(
            mode=TradingMode.SIMULATION,
            symbols=["AAPL"],
            update_interval_seconds=1.0  # Fast for testing
        )
        self.portfolio_manager = PortfolioManager({
            'initial_cash': 100000,
            'max_drawdown': 0.15,
            'max_daily_loss': 0.05,
            'max_position_size': 0.10
        })
        self.engine = LiveTradingEngine(
            config=self.config,
            strategy_manager=StrategyManager(),
            portfolio_manager=self.portfolio_manager
        )

    def test_initialization(self):
        """Test live trading engine initialization"""
        self.assertIsNotNone(self.engine.config)
        self.assertIsNotNone(self.engine.strategy_manager)
        self.assertIsNotNone(self.engine.portfolio_manager)
        self.assertEqual(self.engine.state.value, "stopped")

    def test_get_engine_status(self):
        """Test getting engine status"""
        status = self.engine.get_engine_status()
        self.assertIsInstance(status, dict)
        self.assertIn('state', status)
        self.assertIn('mode', status)
        self.assertIn('symbols', status)

    def test_get_execution_history(self):
        """Test getting execution history"""
        history = self.engine.get_execution_history()
        self.assertIsInstance(history, list)

    def test_generate_mock_data(self):
        """Test mock data generation"""
        data = self.engine._generate_mock_data("AAPL")
        self.assertIsInstance(data, dict)
        self.assertIn('symbol', data)
        self.assertIn('close', data)
        self.assertIn('timestamp', data)

    def test_calculate_position_size(self):
        """Test position size calculation"""
        size = self.engine._calculate_position_size("AAPL", "buy", 0.8)
        self.assertIsInstance(size, int)
        self.assertGreaterEqual(size, 0)

    def test_check_signal_risk_limits(self):
        """Test risk limit checking"""
        from trading_engine import ExecutionResult

        result = ExecutionResult(
            strategy_name="test",
            symbol="AAPL",
            signal="buy",
            confidence=0.8,
            execution_time_ms=100.0,
            success=True
        )

        can_trade = self.engine._check_signal_risk_limits(result)
        self.assertIsInstance(can_trade, bool)

class TestStructuredLogger(unittest.TestCase):

    def setUp(self):
        self.logger = StructuredLogger(log_file="test.log")

    def test_log_entry(self):
        """Test logging functionality"""
        self.logger.log(
            LogLevel.INFO,
            Component.STRATEGY,
            "Test message",
            data={'key': 'value'}
        )

        metrics = self.logger.get_metrics_summary()
        self.assertIsInstance(metrics, dict)
        self.assertIn('error_count', metrics)

    def test_performance_logging(self):
        """Test performance metric logging"""
        self.logger.log_performance_metric("test_operation", 150.0, Component.STRATEGY)

        metrics = self.logger.get_metrics_summary()
        self.assertGreater(metrics['avg_strategy_execution_time'], 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for trading engine components"""

    def setUp(self):
        from trading_engine import (
            StrategyManager, AdaptiveRSIMACDStrategy,
            LiveTradingConfig, TradingMode, LiveTradingEngine
        )

        # Setup strategy
        self.strategy_manager = StrategyManager()
        config = {
            'name': 'test_adaptive_rsi_macd',
            'strategy_params': {
                'rsi_period': 14,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9
            }
        }
        self.strategy_manager.load_strategy('test_strategy', AdaptiveRSIMACDStrategy, config)

        # Setup portfolio
        self.portfolio_manager = PortfolioManager({
            'initial_cash': 100000,
            'max_drawdown': 0.15,
            'max_daily_loss': 0.05,
            'max_position_size': 0.10
        })

        # Setup live engine
        self.live_config = LiveTradingConfig(
            mode=TradingMode.SIMULATION,
            symbols=["AAPL"],
            update_interval_seconds=1.0
        )
        self.live_engine = LiveTradingEngine(
            config=self.live_config,
            strategy_manager=self.strategy_manager,
            portfolio_manager=self.portfolio_manager
        )

    def test_strategy_to_portfolio_integration(self):
        """Test integration between strategy signals and portfolio updates"""
        # Load and activate strategy
        success = self.strategy_manager.activate_strategy('test_strategy')
        self.assertTrue(success)

        # Simulate market data
        market_data = {
            'timestamp': datetime.now(),
            'open': 95,
            'high': 105,
            'low': 95,
            'close': 98,
            'volume': 1000
        }

        # Execute strategy
        result = self.strategy_manager.execute_strategy('test_strategy', market_data)
        self.assertIsNotNone(result)

        # If signal generated, test portfolio update
        if result['signal'] != 'hold':
            success = self.portfolio_manager.update_position(
                "AAPL", 10, 100.0, result['signal']
            )
            self.assertTrue(success)

            # Check portfolio updated
            positions = self.portfolio_manager.get_position_summary()
            self.assertIsInstance(positions, list)

    def test_live_engine_data_flow(self):
        """Test data flow in live trading engine"""
        # Test mock data generation
        data = self.live_engine._generate_mock_data("AAPL")
        self.assertIsInstance(data, dict)
        self.assertEqual(data['symbol'], "AAPL")

        # Test position size calculation
        size = self.live_engine._calculate_position_size("AAPL", "buy", 0.8)
        self.assertIsInstance(size, int)

    def test_error_handling(self):
        """Test error handling in components"""
        # Test invalid strategy execution
        result = self.strategy_manager.execute_strategy('nonexistent', {})
        self.assertIsNone(result)

        # Test portfolio with invalid data
        success = self.portfolio_manager.update_position("AAPL", -1, -100.0, "invalid")
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
