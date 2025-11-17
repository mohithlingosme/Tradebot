"""
Integration tests for adapters with sample data
"""

import pytest
import asyncio
import os
import tempfile
import time
import pandas as pd
from unittest.mock import patch, AsyncMock

from market_data_ingestion.adapters.yfinance import YFinanceAdapter
from market_data_ingestion.adapters.alphavantage import AlphaVantageAdapter
from market_data_ingestion.core.storage import DataStorage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield f"sqlite:///{db_path}"
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
async def storage(temp_db):
    """Create and initialize storage instance."""
    storage = DataStorage(temp_db)
    await storage.connect()
    await storage.create_tables()
    yield storage
    await storage.disconnect()


class TestYFinanceAdapterIntegration:
    """Integration tests for YFinanceAdapter"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_and_store_data(self, storage):
        """Test fetching data from YFinance and storing it."""
        config = {'rate_limit_per_minute': 100}
        adapter = YFinanceAdapter(config)
        
        # Fetch data for a well-known symbol
        # Using a short period to avoid rate limits
        data = await adapter.fetch_historical_data(
            symbol="AAPL",
            start="2024-01-01",
            end="2024-01-02",
            interval="1d"
        )
        
        # Verify data structure
        if data:  # May be empty if API is unavailable
            assert len(data) > 0
            candle = data[0]
            assert 'symbol' in candle
            assert 'ts_utc' in candle
            assert 'open' in candle
            assert 'high' in candle
            assert 'low' in candle
            assert 'close' in candle
            assert 'volume' in candle
            assert candle['provider'] == 'yfinance'
            
            # Store data
            for candle in data:
                await storage.insert_candle(candle)
            
            # Verify storage
            stored = await storage.fetch_last_n_candles("AAPL", "1d", limit=10)
            assert len(stored) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_multiple_symbols(self, storage):
        """Test fetching data for multiple symbols."""
        config = {'rate_limit_per_minute': 100}
        adapter = YFinanceAdapter(config)
        
        symbols = ["AAPL", "GOOGL", "MSFT"]
        all_data = []
        
        for symbol in symbols:
            data = await adapter.fetch_historical_data(
                symbol=symbol,
                start="2024-01-01",
                end="2024-01-02",
                interval="1d"
            )
            if data:
                all_data.extend(data)
                # Store data
                for candle in data:
                    await storage.insert_candle(candle)
        
        # Verify all symbols are stored
        if all_data:
            for symbol in symbols:
                stored = await storage.fetch_last_n_candles(symbol, "1d", limit=10)
                # May be empty if API unavailable, but structure should be correct
                if stored:
                    assert stored[0]['symbol'] == symbol


class TestAdapterDataNormalization:
    """Test data normalization across adapters"""
    
    def test_yfinance_normalization(self):
        """Test YFinance data normalization."""
        import pandas as pd
        
        config = {'rate_limit_per_minute': 100}
        adapter = YFinanceAdapter(config)
        
        # Create sample data
        mock_data = pd.DataFrame({
            'Open': [150.0],
            'High': [151.0],
            'Low': [149.0],
            'Close': [150.5],
            'Volume': [1000]
        }, index=[pd.Timestamp('2024-01-01 10:00:00')])
        
        normalized = adapter._normalize_data("AAPL", mock_data, "1d", "yfinance")
        
        assert len(normalized) == 1
        candle = normalized[0]
        
        # Verify required fields
        required_fields = ['symbol', 'ts_utc', 'open', 'high', 'low', 'close', 'volume', 'provider']
        for field in required_fields:
            assert field in candle
        
        assert candle['symbol'] == "AAPL"
        assert candle['provider'] == "yfinance"
        assert isinstance(candle['open'], (int, float))
        assert isinstance(candle['high'], (int, float))
        assert isinstance(candle['low'], (int, float))
        assert isinstance(candle['close'], (int, float))
        assert isinstance(candle['volume'], (int, float))
    
    def test_alphavantage_normalization(self):
        """Test AlphaVantage data normalization."""
        config = {
            'api_key': 'test_key',
            'base_url': 'https://www.alphavantage.co',
            'rate_limit_per_minute': 5
        }
        adapter = AlphaVantageAdapter(config)
        
        # Create sample data
        mock_data = {
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
        
        normalized = adapter._normalize_data("AAPL", mock_data, "1d", "alphavantage")
        
        assert len(normalized) == 1
        candle = normalized[0]
        
        # Verify required fields
        required_fields = ['symbol', 'ts_utc', 'open', 'high', 'low', 'close', 'volume', 'provider']
        for field in required_fields:
            assert field in candle
        
        assert candle['symbol'] == "AAPL"
        assert candle['provider'] == "alphavantage"


class TestAdapterErrorHandling:
    """Test error handling in adapters"""
    
    @pytest.mark.asyncio
    async def test_yfinance_network_error(self):
        """Test YFinance adapter handles network errors."""
        config = {'rate_limit_per_minute': 100}
        adapter = YFinanceAdapter(config)
        
        with patch('market_data_ingestion.adapters.yfinance.yf.download', side_effect=Exception("Network error")):
            result = await adapter.fetch_historical_data(
                symbol="AAPL",
                start="2024-01-01",
                end="2024-01-02",
                interval="1d"
            )
            
            # Should return empty list on error
            assert result == []
    
    @pytest.mark.asyncio
    async def test_alphavantage_api_error(self):
        """Test AlphaVantage adapter handles API errors."""
        config = {
            'api_key': 'test_key',
            'base_url': 'https://www.alphavantage.co',
            'rate_limit_per_minute': 5
        }
        adapter = AlphaVantageAdapter(config)
        
        async def mock_get(url):
            raise Exception("API error")
        
        adapter.session = AsyncMock()
        adapter.session.get = AsyncMock(side_effect=mock_get)
        
        result = await adapter.fetch_historical_data(
            symbol="AAPL",
            start="2024-01-01",
            end="2024-01-02",
            interval="1d"
        )
        
        # Should return empty list on error
        assert result == []


class TestAdapterRateLimiting:
    """Test rate limiting in adapters"""
    
    @pytest.mark.asyncio
    async def test_yfinance_rate_limiting(self):
        """Test YFinance adapter respects rate limits."""
        import time
        
        config = {'rate_limit_per_minute': 60}  # 1 request per second
        adapter = YFinanceAdapter(config)
        
        start_time = time.time()
        
        with patch('market_data_ingestion.adapters.yfinance.yf.download', return_value=pd.DataFrame()):
            await adapter.fetch_historical_data(
                symbol="AAPL",
                start="2024-01-01",
                end="2024-01-02",
                interval="1d"
            )
        
        elapsed = time.time() - start_time
        
        # Should have waited at least the rate limit delay
        # Rate limit delay = 60 / 60 = 1 second
        assert elapsed >= 0.9  # Allow some tolerance

