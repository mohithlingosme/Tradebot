import unittest
from unittest.mock import patch
from datetime import time, datetime
from risk.risk_manager import RiskManager


class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager(max_daily_loss=200.0, max_position_size=100, trading_end_time=time(15, 15))

    @patch('risk.risk_manager.datetime')
    def test_hard_stop_triggered(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1500, 'side': 'BUY', 'type': 'LIMIT'}
        portfolio_state = {
            'daily_pnl': -250.0,
            'current_positions': {'INFY': 0},
            'available_margin': 10000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertFalse(approved)
        self.assertIn("Hard stop triggered", reason)

    @patch('risk.risk_manager.datetime')
    def test_hard_stop_not_triggered(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1500, 'side': 'BUY', 'type': 'LIMIT'}
        portfolio_state = {
            'daily_pnl': -150.0,
            'current_positions': {'INFY': 0},
            'available_margin': 100000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertTrue(approved)
        self.assertEqual(reason, "OK")

    @patch('risk.risk_manager.datetime')
    def test_time_filter_buy_after_end_time(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 15, 20)  # 3:20 PM
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1500, 'side': 'BUY', 'type': 'LIMIT'}
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 0},
            'available_margin': 10000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertFalse(approved)
        self.assertIn("Trading end time exceeded", reason)

    @patch('risk.risk_manager.datetime')
    def test_time_filter_sell_after_end_time_allowed(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 15, 20)  # 3:20 PM
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1500, 'side': 'SELL', 'type': 'LIMIT'}
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 0},
            'available_margin': 10000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertTrue(approved)  # Should allow SELL

    @patch('risk.risk_manager.datetime')
    def test_time_filter_exit_after_end_time_allowed(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 15, 20)  # 3:20 PM
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1500, 'side': 'BUY', 'type': 'EXIT'}
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 0},
            'available_margin': 10000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertTrue(approved)  # Should allow EXIT

    @patch('risk.risk_manager.datetime')
    def test_position_limit_exceeded_buy(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 60, 'price': 1500, 'side': 'BUY', 'type': 'LIMIT'}
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 50},  # Projected: 50 + 60 = 110 > 100
            'available_margin': 100000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertFalse(approved)
        self.assertIn("Position limit exceeded", reason)

    @patch('risk.risk_manager.datetime')
    def test_position_limit_exceeded_sell(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 60, 'price': 1500, 'side': 'SELL', 'type': 'LIMIT'}
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 50},  # Projected: 50 - 60 = -10, abs(-10) = 10 <= 100
            'available_margin': 100000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertTrue(approved)  # Should be OK

    @patch('risk.risk_manager.datetime')
    def test_margin_insufficient(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1500, 'side': 'BUY', 'type': 'LIMIT'}  # Value: 15000
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 0},
            'available_margin': 10000,  # 15000 > 10000
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertFalse(approved)
        self.assertIn("Insufficient margin", reason)

    @patch('risk.risk_manager.datetime')
    def test_circuit_limit_below_lower(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1300, 'side': 'BUY', 'type': 'LIMIT'}  # 1300 < 1400
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 0},
            'available_margin': 100000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertFalse(approved)
        self.assertIn("below lower circuit", reason)

    @patch('risk.risk_manager.datetime')
    def test_circuit_limit_above_upper(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1700, 'side': 'BUY', 'type': 'LIMIT'}  # 1700 > 1600
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 0},
            'available_margin': 100000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertFalse(approved)
        self.assertIn("above upper circuit", reason)

    @patch('risk.risk_manager.datetime')
    def test_invalid_order_side(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1500, 'side': 'INVALID', 'type': 'LIMIT'}
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 0},
            'available_margin': 100000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertFalse(approved)
        self.assertIn("Invalid order side", reason)

    @patch('risk.risk_manager.datetime')
    def test_valid_order(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2023, 1, 1, 14, 0)  # Before end time
        order = {'symbol': 'INFY', 'qty': 10, 'price': 1500, 'side': 'BUY', 'type': 'LIMIT'}
        portfolio_state = {
            'daily_pnl': 0.0,
            'current_positions': {'INFY': 0},
            'available_margin': 100000,
            'circuit_limits': {'lower_circuit': 1400, 'upper_circuit': 1600}
        }
        approved, reason = self.rm.validate_order(order, portfolio_state)
        self.assertTrue(approved)
        self.assertEqual(reason, "OK")


if __name__ == '__main__':
    unittest.main()
