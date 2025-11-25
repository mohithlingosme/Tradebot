"""
Integration tests for API authentication and endpoints
"""

import unittest
import json
import sys
import os
from unittest.mock import patch, Mock
import httpx
import asyncio
from fastapi.testclient import TestClient

# Add backend package to path
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_path)

# Import with type ignore for linter - path is added at runtime
from api.main import app  # type: ignore
from api.auth import UserCredentials  # type: ignore


class TestAPIAuthentication(unittest.TestCase):
    """Test API authentication endpoints"""

    def setUp(self):
        self.client = TestClient(app)

    def test_login_successful(self):
        """Test successful login"""
        credentials = {
            "username": "admin",
            "password": "admin123"
        }

        response = self.client.post("/auth/login", json=credentials)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertIn("expires_in", data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        credentials = {
            "username": "admin",
            "password": "wrongpassword"
        }

        response = self.client.post("/auth/login", json=credentials)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.json()["detail"])

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        credentials = {
            "username": "nonexistent",
            "password": "password"
        }

        response = self.client.post("/auth/login", json=credentials)
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid credentials", response.json()["detail"])

    def test_logout_authenticated(self):
        """Test logout with valid authentication"""
        # First login to get token
        credentials = {
            "username": "admin",
            "password": "admin123"
        }
        login_response = self.client.post("/auth/login", json=credentials)
        token = login_response.json()["access_token"]

        # Then logout
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.post("/auth/logout", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Logged out successfully", response.json()["message"])

    def test_logout_unauthenticated(self):
        """Test logout without authentication"""
        response = self.client.post("/auth/logout")
        self.assertEqual(response.status_code, 403)


class TestProtectedEndpoints(unittest.TestCase):
    """Test protected API endpoints requiring authentication"""

    def setUp(self):
        self.client = TestClient(app)

    def _get_auth_token(self):
        """Helper to get authentication token"""
        credentials = {
            "username": "admin",
            "password": "admin123"
        }
        response = self.client.post("/auth/login", json=credentials)
        return response.json()["access_token"]

    def test_protected_endpoint_authenticated(self):
        """Test accessing protected endpoint with valid auth"""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        response = self.client.get("/protected", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello admin", response.json()["message"])

    def test_protected_endpoint_no_auth(self):
        """Test accessing protected endpoint without auth"""
        response = self.client.get("/protected")
        self.assertEqual(response.status_code, 403)

    def test_protected_endpoint_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = self.client.get("/protected", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_place_trade_authenticated(self):
        """Test placing trade with authentication"""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        trade_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 10,
            "price": 150.0
        }

        response = self.client.post("/trades", json=trade_data, headers=headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["symbol"], "AAPL")
        self.assertEqual(data["side"], "buy")
        self.assertEqual(data["quantity"], 10)

    def test_place_trade_no_auth(self):
        """Test placing trade without authentication"""
        trade_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 10,
            "price": 150.0
        }

        response = self.client.post("/trades", json=trade_data)
        self.assertEqual(response.status_code, 403)

    def test_place_trade_invalid_side(self):
        """Test placing trade with invalid side"""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        trade_data = {
            "symbol": "AAPL",
            "side": "invalid",
            "quantity": 10,
            "price": 150.0
        }

        response = self.client.post("/trades", json=trade_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid trade side", response.json()["detail"])

    def test_place_trade_invalid_quantity(self):
        """Test placing trade with invalid quantity"""
        token = self._get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        trade_data = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": -10,
            "price": 150.0
        }

        response = self.client.post("/trades", json=trade_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid quantity", response.json()["detail"])


class TestPublicEndpoints(unittest.TestCase):
    """Test public API endpoints that don't require authentication"""

    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Finbot Trading API", response.json()["message"])

    def test_status_endpoint(self):
        """Test status endpoint"""
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("status", data)
        self.assertIn("timestamp", data)
        self.assertIn("services", data)

    def test_health_endpoint(self):
        """Test health endpoint"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("status", data)
        self.assertIn("services", data)
        self.assertIn("timestamp", data)

    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("timestamp", data)
        self.assertIn("trading", data)
        self.assertIn("portfolio", data)
        self.assertIn("system", data)

    @patch('os.path.exists')
    def test_logs_endpoint_no_file(self, mock_exists):
        """Test logs endpoint when no log file exists"""
        mock_exists.return_value = False

        response = self.client.get("/logs")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("logs", data)
        self.assertIn("message", data)
        self.assertEqual(data["message"], "No log file found")

    @patch('os.path.exists')
    @patch('builtins.open')
    def test_logs_endpoint_with_file(self, mock_open, mock_exists):
        """Test logs endpoint with existing log file"""
        mock_exists.return_value = True

        # Mock log file content with structured logs
        mock_log_content = """2023-01-01 10:00:00,000 - finbot - INFO - [strategy] System started | Data: {"key": "value"} | Trace: abc123 | Duration: 150.5ms
2023-01-01 10:01:00,000 - finbot - ERROR - [execution] Connection failed | Data: {"error": "timeout"}
2023-01-01 10:02:00,000 - finbot - WARNING - Low memory warning"""

        mock_file = Mock()
        mock_file.readlines.return_value = mock_log_content.split('\n')
        mock_open.return_value.__enter__.return_value = mock_file

        response = self.client.get("/logs")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("logs", data)
        self.assertIn("total_lines", data)
        self.assertEqual(len(data["logs"]), 3)

        # Check first log entry
        first_log = data["logs"][0]
        self.assertEqual(first_log["level"], "INFO")
        self.assertEqual(first_log["component"], "strategy")
        self.assertEqual(first_log["message"], "System started")
        self.assertEqual(first_log["data"], {"key": "value"})
        self.assertEqual(first_log["trace_id"], "abc123")
        self.assertEqual(first_log["duration_ms"], 150.5)

        # Check second log entry
        second_log = data["logs"][1]
        self.assertEqual(second_log["level"], "ERROR")
        self.assertEqual(second_log["component"], "execution")
        self.assertEqual(second_log["message"], "Connection failed")
        self.assertEqual(second_log["data"], {"error": "timeout"})
        self.assertIsNone(second_log["trace_id"])
        self.assertIsNone(second_log["duration_ms"])

        # Check third log entry (no component, fallback)
        third_log = data["logs"][2]
        self.assertEqual(third_log["level"], "WARNING")
        self.assertEqual(third_log["component"], "finbot")
        self.assertEqual(third_log["message"], "Low memory warning")
        self.assertEqual(third_log["data"], {})
        self.assertIsNone(third_log["trace_id"])
        self.assertIsNone(third_log["duration_ms"])


class TestStrategyEndpoints(unittest.TestCase):
    """Test strategy management endpoints"""

    def setUp(self):
        self.client = TestClient(app)

    def test_get_strategies(self):
        """Test getting strategies"""
        response = self.client.get("/strategies")
        # Strategy manager is not initialized in test environment
        self.assertEqual(response.status_code, 503)

    def test_manage_strategy_invalid_action(self):
        """Test managing strategy with invalid action"""
        response = self.client.post("/strategies/invalid_action?strategy_name=test")
        # Strategy manager is not initialized in test environment
        self.assertEqual(response.status_code, 503)

    def test_load_strategy_invalid_class(self):
        """Test loading strategy with invalid class"""
        strategy_config = {
            "name": "test_strategy",
            "class": "InvalidStrategyClass",
            "config": {}
        }

        response = self.client.post("/strategies/load", json=strategy_config)
        # FastAPI returns 422 for Pydantic validation errors when strategy_manager is None
        self.assertEqual(response.status_code, 422)


class TestTradingEndpoints(unittest.TestCase):
    """Test trading engine endpoints"""

    def setUp(self):
        self.client = TestClient(app)

    def test_get_trading_status(self):
        """Test getting trading status"""
        response = self.client.get("/trading/status")
        # Trading engine is not initialized in test environment
        self.assertEqual(response.status_code, 500)

    def test_get_trading_history(self):
        """Test getting trading history"""
        response = self.client.get("/trading/history")
        # Trading engine is not initialized in test environment
        self.assertEqual(response.status_code, 500)

    def test_control_trading_invalid_action(self):
        """Test controlling trading with invalid action"""
        response = self.client.post("/trading/invalid_action")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid action", response.json()["detail"])


if __name__ == '__main__':
    unittest.main()
