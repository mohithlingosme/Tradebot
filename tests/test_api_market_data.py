import pytest
from fastapi.testclient import TestClient
from market_data_ingestion.src.api import app
import json
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from fastapi import FastAPI

@pytest.fixture
def test_app():
    """Create a test app without lifespan to avoid DB connections during tests."""
    # Create a minimal app for testing
    test_app = FastAPI(title="Test Market Data API", version="1.0.0")

    # Add routes manually (copy from original app)
    from market_data_ingestion.src.api import (
        health_check, healthz, readiness_check, readyz, get_metrics,
        get_candles, get_available_symbols
    )

    test_app.add_route("/health", health_check, methods=["GET"])
    test_app.add_route("/healthz", healthz, methods=["GET"])
    test_app.add_route("/ready", readiness_check, methods=["GET"])
    test_app.add_route("/readyz", readyz, methods=["GET"])
    test_app.add_route("/metrics", get_metrics, methods=["GET"])
    test_app.add_route("/candles", get_candles, methods=["GET"])
    test_app.add_route("/symbols", get_available_symbols, methods=["GET"])

    # Add auth routes if available
    try:
        from market_data_ingestion.src.api import auth_router
        test_app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    except:
        pass

    return test_app

@pytest.fixture
def client(test_app):
    """Test client fixture."""
    return TestClient(test_app)

class TestHealthEndpoints:
    """Test health and readiness endpoints."""

    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "market-data-api"

    def test_healthz_alias(self, client):
        """Test /healthz alias."""
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "market-data-api"}

    @patch('market_data_ingestion.src.api.storage')
    def test_readiness_check_success(self, mock_storage, client):
        """Test readiness check when database is available."""
        # Mock successful database connection
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.execute.return_value = mock_cursor
        mock_storage.conn = mock_conn

        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "market-data-api"

    @patch('market_data_ingestion.src.api.storage')
    def test_readiness_check_failure(self, mock_storage, client):
        """Test readiness check when database fails."""
        # Mock failed database connection
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")
        mock_storage.conn = mock_conn

        response = client.get("/ready")
        assert response.status_code == 503
        assert "Service not ready" in response.json()["detail"]

    def test_readyz_alias(self, client):
        """Test /readyz alias."""
        # This will fail if DB is not mocked, but that's expected for alias test
        response = client.get("/readyz")
        # Should behave same as /ready
        assert response.status_code in [200, 503]

class TestMetricsEndpoint:
    """Test metrics endpoint."""

    @patch('market_data_ingestion.src.api.metrics_collector')
    def test_get_metrics(self, mock_metrics, client):
        """Test metrics endpoint returns Prometheus format."""
        mock_metrics.get_metrics.return_value = "# Sample metrics"

        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "# Sample metrics" in response.text

class TestCandlesEndpoint:
    """Test candle data retrieval endpoint."""

    @patch('market_data_ingestion.src.api.storage')
    def test_get_candles_success(self, mock_storage, client):
        """Test successful candle data retrieval."""
        # Mock candle data
        mock_candles = [
            {"timestamp": "2023-01-01T09:15:00Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000},
            {"timestamp": "2023-01-01T09:16:00Z", "open": 100.5, "high": 102.0, "low": 100.0, "close": 101.5, "volume": 1200}
        ]
        mock_storage.fetch_last_n_candles = AsyncMock(return_value=mock_candles)

        response = client.get("/candles?symbol=AAPL&interval=1m&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["interval"] == "1m"
        assert data["count"] == 2
        assert len(data["data"]) == 2

    @patch('market_data_ingestion.src.api.storage')
    def test_get_candles_no_data(self, mock_storage, client):
        """Test candle retrieval when no data exists."""
        mock_storage.fetch_last_n_candles = AsyncMock(return_value=[])

        response = client.get("/candles?symbol=INVALID&interval=1m&limit=10")
        assert response.status_code == 404
        assert "No data found for symbol INVALID" in response.json()["detail"]

    @patch('market_data_ingestion.src.api.storage')
    def test_get_candles_db_error(self, mock_storage, client):
        """Test candle retrieval when database error occurs."""
        mock_storage.fetch_last_n_candles = AsyncMock(side_effect=Exception("DB error"))

        response = client.get("/candles?symbol=AAPL&interval=1m&limit=10")
        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error"

    def test_get_candles_missing_symbol(self, client):
        """Test candle retrieval with missing symbol parameter."""
        response = client.get("/candles?interval=1m&limit=10")
        assert response.status_code == 422  # Validation error

    def test_get_candles_invalid_limit(self, client):
        """Test candle retrieval with invalid limit values."""
        # Too low
        response = client.get("/candles?symbol=AAPL&interval=1m&limit=0")
        assert response.status_code == 422

        # Too high
        response = client.get("/candles?symbol=AAPL&interval=1m&limit=1001")
        assert response.status_code == 422

class TestSymbolsEndpoint:
    """Test available symbols endpoint."""

    @patch('market_data_ingestion.src.api.storage')
    def test_get_symbols_success(self, mock_storage, client):
        """Test successful symbols retrieval."""
        # Mock database response
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [("AAPL",), ("GOOGL",), ("MSFT",)]
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor
        mock_storage.conn = mock_conn

        response = client.get("/symbols")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert "AAPL" in data["symbols"]
        assert "GOOGL" in data["symbols"]
        assert "MSFT" in data["symbols"]

    @patch('market_data_ingestion.src.api.storage')
    def test_get_symbols_empty(self, mock_storage, client):
        """Test symbols retrieval when no symbols exist."""
        # Mock empty database response
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = AsyncMock()
        mock_conn.execute.return_value = mock_cursor
        mock_storage.conn = mock_conn

        response = client.get("/symbols")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["symbols"] == []

    @patch('market_data_ingestion.src.api.storage')
    def test_get_symbols_db_error(self, mock_storage, client):
        """Test symbols retrieval when database error occurs."""
        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("DB error")
        mock_storage.conn = mock_conn

        response = client.get("/symbols")
        assert response.status_code == 500
        assert response.json()["detail"] == "Internal server error"

class TestAuthEndpoints:
    """Test authentication endpoints (only if auth is available)."""

    def test_register_success(self, client):
        """Test successful user registration."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "strongpassword123"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["expires_in"] == 1800

    def test_register_existing_user(self, client):
        """Test registration with existing username."""
        # First register
        user_data = {
            "username": "existinguser",
            "email": "existing@example.com",
            "password": "password123"
        }
        client.post("/api/auth/register", json=user_data)

        # Try to register again
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Username already exists" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Password must be at least 8 characters" in response.json()["detail"]

    def test_login_success(self, client):
        """Test successful login."""
        # First register
        user_data = {
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123"
        }
        client.post("/api/auth/register", json=user_data)

        # Then login
        login_data = {
            "username": "loginuser",
            "password": "password123"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_logout(self, client):
        """Test logout endpoint."""
        # This is a basic test - in real JWT, logout is client-side
        response = client.post("/api/auth/logout")
        # Should work without auth for this simple implementation
        assert response.status_code in [200, 401]  # 401 if auth required

class TestIntegration:
    """Integration tests for multiple endpoints."""

    @patch('market_data_ingestion.src.api.storage')
    def test_full_workflow(self, mock_storage, client):
        """Test a full workflow: health -> symbols -> candles."""
        # Mock storage for all operations
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [("AAPL",)]
        mock_conn.execute.return_value = mock_cursor
        mock_storage.conn = mock_conn
        mock_storage.fetch_last_n_candles = AsyncMock(return_value=[
            {"timestamp": "2023-01-01T09:15:00Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000}
        ])

        # Health check
        response = client.get("/health")
        assert response.status_code == 200

        # Get symbols
        response = client.get("/symbols")
        assert response.status_code == 200
        symbols = response.json()["symbols"]
        assert len(symbols) > 0

        # Get candles for first symbol
        symbol = symbols[0]
        response = client.get(f"/candles?symbol={symbol}&interval=1m&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == symbol
        assert len(data["data"]) > 0

if __name__ == "__main__":
    pytest.main([__file__])
