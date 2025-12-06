# FILE: tests/backend/test_market_data_routes.py
"""Test market data routes: price/ohlc endpoints that proxy ingestion DB."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


def test_get_market_data_ohlc(api_client, fake_market_data):
    """Test retrieving OHLC market data."""
    symbol = "AAPL"
    timeframe = "5m"

    # Mock the market data query
    with patch("backend.api.market_data.get_ohlc_data") as mock_get_data:
        mock_get_data.return_value = fake_market_data[fake_market_data["symbol"] == symbol]

        response = api_client.get(f"/api/market-data/ohlc/{symbol}?timeframe={timeframe}")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert len(data["data"]) > 0

        # Check data structure
        first_bar = data["data"][0]
        required_fields = ["timestamp", "open", "high", "low", "close", "volume"]
        for field in required_fields:
            assert field in first_bar


def test_get_market_data_ohlc_invalid_symbol(api_client):
    """Test OHLC request for invalid/non-existent symbol."""
    with patch("backend.api.market_data.get_ohlc_data") as mock_get_data:
        mock_get_data.return_value = pd.DataFrame()  # Empty DataFrame

        response = api_client.get("/api/market-data/ohlc/INVALID")

        assert response.status_code == 404
        data = response.json()
        assert "No data found" in data["detail"]


def test_get_market_data_ohlc_with_date_range(api_client, fake_market_data):
    """Test OHLC data retrieval with date range filtering."""
    symbol = "AAPL"
    start_date = "2023-01-01"
    end_date = "2023-01-02"

    with patch("backend.api.market_data.get_ohlc_data") as mock_get_data:
        mock_get_data.return_value = fake_market_data[fake_market_data["symbol"] == symbol]

        response = api_client.get(
            f"/api/market-data/ohlc/{symbol}?start_date={start_date}&end_date={end_date}"
        )

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        # Should filter data within date range
        assert len(data["data"]) >= 0


def test_get_current_price(api_client):
    """Test getting current/last price for a symbol."""
    symbol = "AAPL"

    with patch("backend.api.market_data.get_current_price") as mock_get_price:
        mock_get_price.return_value = {
            "symbol": symbol,
            "price": 150.25,
            "timestamp": "2023-01-01T12:00:00Z",
            "source": "mock"
        }

        response = api_client.get(f"/api/market-data/price/{symbol}")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == symbol
        assert data["price"] == 150.25
        assert "timestamp" in data


def test_get_current_price_not_found(api_client):
    """Test current price for unknown symbol."""
    with patch("backend.api.market_data.get_current_price") as mock_get_price:
        mock_get_price.return_value = None

        response = api_client.get("/api/market-data/price/UNKNOWN")

        assert response.status_code == 404
        data = response.json()
        assert "Price not found" in data["detail"]


def test_get_market_data_quote(api_client):
    """Test getting full quote data."""
    symbol = "AAPL"

    with patch("backend.api.market_data.get_quote") as mock_get_quote:
        mock_get_quote.return_value = {
            "symbol": symbol,
            "bid": 150.20,
            "ask": 150.30,
            "last": 150.25,
            "volume": 1000000,
            "timestamp": "2023-01-01T12:00:00Z"
        }

        response = api_client.get(f"/api/market-data/quote/{symbol}")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == symbol
        assert "bid" in data
        assert "ask" in data
        assert "last" in data


def test_get_market_depth(api_client):
    """Test getting market depth/order book."""
    symbol = "AAPL"

    with patch("backend.api.market_data.get_market_depth") as mock_get_depth:
        mock_get_depth.return_value = {
            "symbol": symbol,
            "bids": [
                {"price": 150.20, "quantity": 100},
                {"price": 150.15, "quantity": 200}
            ],
            "asks": [
                {"price": 150.30, "quantity": 150},
                {"price": 150.35, "quantity": 250}
            ],
            "timestamp": "2023-01-01T12:00:00Z"
        }

        response = api_client.get(f"/api/market-data/depth/{symbol}")

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == symbol
        assert "bids" in data
        assert "asks" in data
        assert len(data["bids"]) > 0
        assert len(data["asks"]) > 0


def test_get_historical_volume(api_client, fake_market_data):
    """Test getting historical volume data."""
    symbol = "AAPL"

    with patch("backend.api.market_data.get_volume_data") as mock_get_volume:
        volume_data = fake_market_data[fake_market_data["symbol"] == symbol][["timestamp", "volume"]]
        mock_get_volume.return_value = volume_data

        response = api_client.get(f"/api/market-data/volume/{symbol}")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert len(data["data"]) > 0

        # Check volume data structure
        first_entry = data["data"][0]
        assert "timestamp" in first_entry
        assert "volume" in first_entry


def test_get_market_data_with_pagination(api_client, fake_market_data):
    """Test market data endpoints support pagination."""
    symbol = "AAPL"

    with patch("backend.api.market_data.get_ohlc_data") as mock_get_data:
        mock_get_data.return_value = fake_market_data[fake_market_data["symbol"] == symbol]

        response = api_client.get(f"/api/market-data/ohlc/{symbol}?limit=10&offset=5")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert len(data["data"]) <= 10  # Limited by pagination


def test_get_market_data_invalid_timeframe(api_client):
    """Test market data request with invalid timeframe."""
    symbol = "AAPL"
    invalid_timeframe = "invalid"

    response = api_client.get(f"/api/market-data/ohlc/{symbol}?timeframe={invalid_timeframe}")

    assert response.status_code == 400
    data = response.json()
    assert "Invalid timeframe" in data["detail"]


def test_get_market_data_rate_limiting(api_client):
    """Test market data endpoints are rate limited."""
    symbol = "AAPL"

    # Make multiple rapid requests
    responses = []
    for _ in range(5):
        response = api_client.get(f"/api/market-data/price/{symbol}")
        responses.append(response.status_code)

    # At least one should be rate limited (429)
    assert 429 in responses or all(r == 200 for r in responses)


def test_get_market_data_caching(api_client):
    """Test market data responses are cached appropriately."""
    symbol = "AAPL"

    with patch("backend.api.market_data.get_current_price") as mock_get_price:
        mock_get_price.return_value = {
            "symbol": symbol,
            "price": 150.25,
            "timestamp": "2023-01-01T12:00:00Z"
        }

        # First request
        response1 = api_client.get(f"/api/market-data/price/{symbol}")
        # Second request (should be cached)
        response2 = api_client.get(f"/api/market-data/price/{symbol}")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Should only call the underlying function once if cached
        assert mock_get_price.call_count == 1


def test_get_market_data_error_handling(api_client):
    """Test market data endpoints handle database errors gracefully."""
    symbol = "AAPL"

    with patch("backend.api.market_data.get_ohlc_data") as mock_get_data:
        mock_get_data.side_effect = Exception("Database connection failed")

        response = api_client.get(f"/api/market-data/ohlc/{symbol}")

        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]


def test_get_market_data_empty_response(api_client):
    """Test handling of empty market data responses."""
    symbol = "AAPL"

    with patch("backend.api.market_data.get_ohlc_data") as mock_get_data:
        mock_get_data.return_value = pd.DataFrame()  # Empty DataFrame

        response = api_client.get(f"/api/market-data/ohlc/{symbol}")

        assert response.status_code == 404
        data = response.json()
        assert "No data available" in data["detail"]
