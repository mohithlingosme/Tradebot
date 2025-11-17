"""
Unit tests for market data adapters
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import pandas as pd
from datetime import datetime

from market_data_ingestion.adapters.yfinance import YFinanceAdapter
from market_data_ingestion.adapters.alphavantage import AlphaVantageAdapter
from market_data_ingestion.adapters.kite_ws import KiteWebSocketAdapter


class TestYFinanceAdapter:
    """Test YFinanceAdapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create YFinanceAdapter instance."""
        config = {'rate_limit_per_minute': 100}
        return YFinanceAdapter(config)
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_success(self, adapter):
        """Test successful data fetch."""
        # Mock yfinance download
        mock_data = pd.DataFrame({
            'Open': [150.0],
            'High': [151.0],
            'Low': [149.0],
            'Close': [150.5],
            'Volume': [1000]
        }, index=[pd.Timestamp('2024-01-01 10:00:00')])
        
        with patch('market_data_ingestion.adapters.yfinance.yf.download', return_value=mock_data):
            result = await adapter.fetch_historical_data(
                symbol="AAPL",
                start="2024-01-01",
                end="2024-01-02",
                interval="1d"
            )
            
            assert len(result) == 1
            assert result[0]['symbol'] == "AAPL"
            assert result[0]['open'] == 150.0
            assert result[0]['high'] == 151.0
            assert result[0]['low'] == 149.0
            assert result[0]['close'] == 150.5
            assert result[0]['volume'] == 1000
            assert result[0]['provider'] == "yfinance"
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_error(self, adapter):
        """Test error handling in data fetch."""
        with patch('market_data_ingestion.adapters.yfinance.yf.download', side_effect=Exception("API Error")):
            result = await adapter.fetch_historical_data(
                symbol="AAPL",
                start="2024-01-01",
                end="2024-01-02",
                interval="1d"
            )
            
            assert result == []
    
    @pytest.mark.asyncio
    async def test_realtime_connect_not_implemented(self, adapter):
        """Test that realtime_connect raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="yfinance does not support realtime data"):
            await adapter.realtime_connect(["AAPL"])
    
    def test_normalize_data(self, adapter):
        """Test data normalization."""
        mock_data = pd.DataFrame({
            'Open': [150.0, 151.0],
            'High': [151.0, 152.0],
            'Low': [149.0, 150.0],
            'Close': [150.5, 151.5],
            'Volume': [1000, 1200]
        }, index=[pd.Timestamp('2024-01-01 10:00:00'), pd.Timestamp('2024-01-01 10:01:00')])
        
        result = adapter._normalize_data("AAPL", mock_data, "1m", "yfinance")
        
        assert len(result) == 2
        assert all(item['symbol'] == "AAPL" for item in result)
        assert all(item['provider'] == "yfinance" for item in result)
        assert all('open' in item for item in result)
        assert all('high' in item for item in result)
        assert all('low' in item for item in result)
        assert all('close' in item for item in result)
        assert all('volume' in item for item in result)


class TestAlphaVantageAdapter:
    """Test AlphaVantageAdapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create AlphaVantageAdapter instance."""
        config = {
            'api_key': 'test_key',
            'base_url': 'https://www.alphavantage.co',
            'rate_limit_per_minute': 5
        }
        return AlphaVantageAdapter(config)
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_daily(self, adapter):
        """Test fetching daily data."""
        mock_response_data = {
            "Time Series (Daily)": {
                "2024-01-01": {
                    "1. open": "150.0",
                    "2. high": "151.0",
                    "3. low": "149.0",
                    "4. close": "150.5",
                    "5. volume": "1000"
                }
            }
        }
        
        async def mock_get(url):
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.raise_for_status = MagicMock()
            return mock_response
        
        adapter.session = AsyncMock()
        adapter.session.get = AsyncMock(side_effect=mock_get)
        
        result = await adapter.fetch_historical_data(
            symbol="AAPL",
            start="2024-01-01",
            end="2024-01-02",
            interval="1d"
        )
        
        assert len(result) == 1
        assert result[0]['symbol'] == "AAPL"
        assert result[0]['open'] == "150.0"
        assert result[0]['provider'] == "alphavantage"
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_intraday(self, adapter):
        """Test fetching intraday data."""
        mock_response_data = {
            "Time Series (1m)": {
                "2024-01-01 10:00:00": {
                    "1. open": "150.0",
                    "2. high": "151.0",
                    "3. low": "149.0",
                    "4. close": "150.5",
                    "5. volume": "1000"
                }
            }
        }
        
        async def mock_get(url):
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_response.raise_for_status = MagicMock()
            return mock_response
        
        adapter.session = AsyncMock()
        adapter.session.get = AsyncMock(side_effect=mock_get)
        
        result = await adapter.fetch_historical_data(
            symbol="AAPL",
            start="2024-01-01",
            end="2024-01-01",
            interval="1m"
        )
        
        assert len(result) == 1
        assert result[0]['symbol'] == "AAPL"
    
    @pytest.mark.asyncio
    async def test_fetch_historical_data_error(self, adapter):
        """Test error handling."""
        async def mock_get(url):
            raise Exception("API Error")
        
        adapter.session = AsyncMock()
        adapter.session.get = AsyncMock(side_effect=mock_get)
        
        result = await adapter.fetch_historical_data(
            symbol="AAPL",
            start="2024-01-01",
            end="2024-01-02",
            interval="1d"
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_realtime_connect_not_implemented(self, adapter):
        """Test that realtime_connect raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="Alpha Vantage does not support realtime data"):
            await adapter.realtime_connect(["AAPL"])
    
    @pytest.mark.asyncio
    async def test_context_manager(self, adapter):
        """Test async context manager."""
        async with adapter as a:
            assert a == adapter
            assert adapter.session is not None
        
        # Session should be closed after context exit
        adapter.session.close.assert_called_once()


class TestKiteWebSocketAdapter:
    """Test KiteWebSocketAdapter"""
    
    @pytest.fixture
    def adapter(self):
        """Create KiteWebSocketAdapter instance."""
        config = {
            'websocket_url': 'ws://localhost:8765',
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'heartbeat_interval': 30,
            'reconnect_interval': 5
        }
        return KiteWebSocketAdapter(config)
    
    @pytest.mark.asyncio
    async def test_authenticate(self, adapter):
        """Test authentication."""
        result = await adapter.authenticate()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_subscribe(self, adapter):
        """Test subscription to symbols."""
        symbols = ["AAPL", "GOOGL"]
        await adapter.subscribe(symbols)
        assert adapter.symbols == symbols
    
    @pytest.mark.asyncio
    async def test_context_manager(self, adapter):
        """Test async context manager."""
        adapter.ws = AsyncMock()
        adapter.ws.close = AsyncMock()
        
        async with adapter:
            pass
        
        adapter.ws.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_tick(self, adapter):
        """Test processing tick message."""
        message = {
            "type": "tick",
            "symbol": "AAPL",
            "price": 150.0,
            "qty": 100,
            "timestamp": "2024-01-01T10:00:00Z"
        }
        
        # Mock callback
        callback_called = []
        
        async def mock_callback(tick):
            callback_called.append(tick)
        
        adapter.on_tick = mock_callback
        
        await adapter.process_message(str(message).replace("'", '"'))
        
        # Note: This test may need adjustment based on actual implementation
        # The process_message method may need to parse JSON

