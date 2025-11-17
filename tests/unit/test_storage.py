"""
Unit tests for DataStorage class
"""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime

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


class TestDataStorage:
    """Test DataStorage class"""
    
    @pytest.mark.asyncio
    async def test_connect_sqlite(self, temp_db):
        """Test connecting to SQLite database."""
        storage = DataStorage(temp_db)
        await storage.connect()
        assert storage.conn is not None
        assert storage.db_type == 'sqlite'
        await storage.disconnect()
    
    @pytest.mark.asyncio
    async def test_create_tables(self, storage):
        """Test table creation."""
        # Tables should be created in fixture
        # Verify by checking if we can query
        cursor = await storage.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candles'")
        row = await cursor.fetchone()
        await cursor.close()
        assert row is not None
    
    @pytest.mark.asyncio
    async def test_insert_candle(self, storage):
        """Test inserting a candle."""
        candle = {
            "symbol": "AAPL",
            "ts_utc": "2024-01-01T10:00:00Z",
            "open": 150.0,
            "high": 151.0,
            "low": 149.0,
            "close": 150.5,
            "volume": 1000,
            "provider": "yfinance"
        }
        
        await storage.insert_candle(candle)
        
        # Verify insertion
        cursor = await storage.conn.execute(
            "SELECT * FROM candles WHERE symbol = ?",
            ("AAPL",)
        )
        row = await cursor.fetchone()
        await cursor.close()
        
        assert row is not None
        assert row[1] == "AAPL"  # symbol
        assert row[2] == "2024-01-01T10:00:00Z"  # ts_utc
        assert row[3] == 150.0  # open
    
    @pytest.mark.asyncio
    async def test_insert_duplicate_candle(self, storage):
        """Test inserting duplicate candle (should be ignored)."""
        candle = {
            "symbol": "AAPL",
            "ts_utc": "2024-01-01T10:00:00Z",
            "open": 150.0,
            "high": 151.0,
            "low": 149.0,
            "close": 150.5,
            "volume": 1000,
            "provider": "yfinance"
        }
        
        # Insert twice
        await storage.insert_candle(candle)
        await storage.insert_candle(candle)
        
        # Verify only one row exists
        cursor = await storage.conn.execute(
            "SELECT COUNT(*) FROM candles WHERE symbol = ?",
            ("AAPL",)
        )
        count = (await cursor.fetchone())[0]
        await cursor.close()
        
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_fetch_last_n_candles(self, storage):
        """Test fetching last N candles."""
        # Insert multiple candles
        candles = [
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
                "symbol": "AAPL",
                "ts_utc": "2024-01-01T10:02:00Z",
                "open": 151.5,
                "high": 153.0,
                "low": 151.0,
                "close": 152.5,
                "volume": 1300,
                "provider": "yfinance"
            }
        ]
        
        for candle in candles:
            await storage.insert_candle(candle)
        
        # Fetch last 2 candles
        result = await storage.fetch_last_n_candles("AAPL", "1m", limit=2)
        
        assert len(result) == 2
        # Should be ordered by timestamp DESC, so most recent first
        assert result[0]['ts_utc'] == "2024-01-01T10:02:00Z"
        assert result[1]['ts_utc'] == "2024-01-01T10:01:00Z"
    
    @pytest.mark.asyncio
    async def test_fetch_last_n_candles_empty(self, storage):
        """Test fetching candles when none exist."""
        result = await storage.fetch_last_n_candles("INVALID", "1m", limit=10)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_fetch_last_n_candles_different_symbols(self, storage):
        """Test fetching candles for different symbols."""
        # Insert candles for different symbols
        candles = [
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
        
        for candle in candles:
            await storage.insert_candle(candle)
        
        # Fetch AAPL candles
        aapl_result = await storage.fetch_last_n_candles("AAPL", "1m", limit=10)
        assert len(aapl_result) == 1
        assert aapl_result[0]['symbol'] == "AAPL"
        
        # Fetch GOOGL candles
        googl_result = await storage.fetch_last_n_candles("GOOGL", "1m", limit=10)
        assert len(googl_result) == 1
        assert googl_result[0]['symbol'] == "GOOGL"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, storage):
        """Test successful health check."""
        result = await storage.health_check()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check failure."""
        storage = DataStorage("sqlite:///nonexistent.db")
        # Don't connect, so health check should fail
        result = await storage.health_check()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self, temp_db):
        """Test disconnecting from database."""
        storage = DataStorage(temp_db)
        await storage.connect()
        assert storage.conn is not None
        
        await storage.disconnect()
        # Connection should be closed
        # In SQLite, we can't directly check if connection is closed,
        # but we can verify by trying to use it (should raise error)
        with pytest.raises(Exception):
            await storage.conn.execute("SELECT 1")

