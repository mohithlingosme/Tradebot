"""
Integration tests for API endpoints (/candles and /metrics)
"""

import pytest
import asyncio
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

# Add market_data_ingestion to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from market_data_ingestion.src.api import app
from market_data_ingestion.core.storage import DataStorage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def storage_with_data(temp_db):
    """Create storage instance with test data."""
    storage = DataStorage(f"sqlite:///{temp_db}")
    await storage.connect()
    await storage.create_tables()
    
    # Insert test candles
    test_candles = [
        {
            "symbol": "AAPL",
            "ts_utc": "2024-01-01T10:00:00Z",
            "open": 150.0,
            "high": 151.0,
            "low": 149.0,
            "close": 150.5,
            "volume": 1000,
            "provider": "yfinance"
        },
        {
            "symbol": "AAPL",
            "ts_utc": "2024-01-01T10:01:00Z",
            "open": 150.5,
            "high": 152.0,
            "low": 150.0,
            "close": 151.5,
            "volume": 1200,
            "provider": "yfinance"
        },
        {
            "symbol": "GOOGL",
            "ts_utc": "2024-01-01T10:00:00Z",
            "open": 2800.0,
            "high": 2810.0,
            "low": 2795.0,
            "close": 2805.0,
            "volume": 500,
            "provider": "yfinance"
        }
    ]
    
    for candle in test_candles:
        await storage.insert_candle(candle)
    
    yield storage
    
    await storage.disconnect()


@pytest.fixture
def client(temp_db):
    """Create a test client with mocked storage."""
    with patch('market_data_ingestion.src.api.storage') as mock_storage:
        # Create a real storage instance for the mock
        storage = DataStorage(f"sqlite:///{temp_db}")
        
        async def connect():
            await storage.connect()
            await storage.create_tables()
            # Insert test data
            test_candles = [
                {
                    "symbol": "AAPL",
                    "ts_utc": "2024-01-01T10:00:00Z",
                    "open": 150.0,
                    "high": 151.0,
                    "low": 149.0,
                    "close": 150.5,
                    "volume": 1000,
                    "provider": "yfinance"
                },
                {
                    "symbol": "AAPL",
                    "ts_utc": "2024-01-01T10:01:00Z",
                    "open": 150.5,
                    "high": 152.0,
                    "low": 150.0,
                    "close": 151.5,
                    "volume": 1200,
                    "provider": "yfinance"
                }
            ]
            for candle in test_candles:
                await storage.insert_candle(candle)
        
        async def disconnect():
            await storage.disconnect()
        
        mock_storage.connect = AsyncMock(side_effect=connect)
        mock_storage.disconnect = AsyncMock(side_effect=disconnect)
        mock_storage.create_tables = AsyncMock()
        mock_storage.fetch_last_n_candles = storage.fetch_last_n_candles
        mock_storage.conn = storage.conn
        
        # Initialize storage
        asyncio.run(storage.connect())
        asyncio.run(storage.create_tables())
        test_candles = [
            {
                "symbol": "AAPL",
                "ts_utc": "2024-01-01T10:00:00Z",
                "open": 150.0,
                "high": 151.0,
                "low": 149.0,
                "close": 150.5,
                "volume": 1000,
                "provider": "yfinance"
            },
            {
                "symbol": "AAPL",
                "ts_utc": "2024-01-01T10:01:00Z",
                "open": 150.5,
                "high": 152.0,
                "low": 150.0,
                "close": 151.5,
                "volume": 1200,
                "provider": "yfinance"
            }
        ]
        for candle in test_candles:
            asyncio.run(storage.insert_candle(candle))
        
        yield TestClient(app)
        
        asyncio.run(storage.disconnect())


class TestCandlesEndpoint:
    """Test /candles endpoint"""
    
    def test_get_candles_success(self, client):
        """Test successful retrieval of candles."""
        response = client.get("/candles?symbol=AAPL&interval=1m&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert "interval" in data
        assert "count" in data
        assert "data" in data
        assert data["symbol"] == "AAPL"
        assert data["interval"] == "1m"
        assert data["count"] == 2
        assert len(data["data"]) == 2
        
        # Verify candle structure
        candle = data["data"][0]
        assert "symbol" in candle
        assert "ts_utc" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert "volume" in candle
    
    def test_get_candles_with_limit(self, client):
        """Test candles endpoint with limit parameter."""
        response = client.get("/candles?symbol=AAPL&interval=1m&limit=1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] == 1
        assert len(data["data"]) == 1
    
    def test_get_candles_not_found(self, client):
        """Test candles endpoint when symbol not found."""
        response = client.get("/candles?symbol=INVALID&interval=1m&limit=10")
        assert response.status_code == 404
        assert "No data found" in response.json()["detail"]
    
    def test_get_candles_missing_symbol(self, client):
        """Test candles endpoint without symbol parameter."""
        response = client.get("/candles?interval=1m&limit=10")
        assert response.status_code == 422  # Validation error
    
    def test_get_candles_invalid_limit(self, client):
        """Test candles endpoint with invalid limit."""
        response = client.get("/candles?symbol=AAPL&interval=1m&limit=0")
        assert response.status_code == 422  # Validation error
        
        response = client.get("/candles?symbol=AAPL&interval=1m&limit=2000")
        assert response.status_code == 422  # Validation error (exceeds max)


class TestMetricsEndpoint:
    """Test /metrics endpoint"""
    
    def test_get_metrics_success(self, client):
        """Test successful retrieval of metrics."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Verify Prometheus format
        content = response.text
        assert "market_data" in content.lower() or len(content) > 0
    
    def test_metrics_format(self, client):
        """Test that metrics are in Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        content = response.text
        # Prometheus metrics typically have lines with # HELP, # TYPE, or metric_name
        assert len(content) > 0


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_ready_check(self, client):
        """Test /ready endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "ready"


class TestSymbolsEndpoint:
    """Test /symbols endpoint"""
    
    def test_get_symbols(self, client):
        """Test getting available symbols."""
        response = client.get("/symbols")
        assert response.status_code == 200
        
        data = response.json()
        assert "symbols" in data
        assert "count" in data
        assert isinstance(data["symbols"], list)

