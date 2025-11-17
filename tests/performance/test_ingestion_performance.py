"""
Performance tests for ingestion pipeline
"""

import pytest
import asyncio
import time
import os
import tempfile
from unittest.mock import patch, AsyncMock

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.core.aggregator import TickAggregator
from market_data_ingestion.adapters.yfinance import YFinanceAdapter


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


class TestStoragePerformance:
    """Performance tests for storage operations"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_bulk_insert_performance(self, storage):
        """Test performance of bulk insert operations."""
        num_candles = 1000
        
        candles = [
            {
                "symbol": "AAPL",
                "ts_utc": f"2024-01-01T10:{i//60:02d}:{i%60:02d}Z",
                "open": 150.0 + i * 0.01,
                "high": 151.0 + i * 0.01,
                "low": 149.0 + i * 0.01,
                "close": 150.5 + i * 0.01,
                "volume": 1000 + i,
                "provider": "yfinance"
            }
            for i in range(num_candles)
        ]
        
        start_time = time.time()
        
        for candle in candles:
            await storage.insert_candle(candle)
        
        elapsed = time.time() - start_time
        
        # Should insert 1000 candles in reasonable time (< 10 seconds)
        assert elapsed < 10.0
        
        # Verify all candles were inserted
        result = await storage.fetch_last_n_candles("AAPL", "1m", limit=num_candles)
        assert len(result) == num_candles
        
        print(f"Inserted {num_candles} candles in {elapsed:.2f} seconds")
        print(f"Rate: {num_candles/elapsed:.2f} candles/second")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_fetch_performance(self, storage):
        """Test performance of fetch operations."""
        # Insert test data
        num_candles = 1000
        candles = [
            {
                "symbol": "AAPL",
                "ts_utc": f"2024-01-01T10:{i//60:02d}:{i%60:02d}Z",
                "open": 150.0 + i * 0.01,
                "high": 151.0 + i * 0.01,
                "low": 149.0 + i * 0.01,
                "close": 150.5 + i * 0.01,
                "volume": 1000 + i,
                "provider": "yfinance"
            }
            for i in range(num_candles)
        ]
        
        for candle in candles:
            await storage.insert_candle(candle)
        
        # Test fetch performance
        start_time = time.time()
        
        for _ in range(100):
            await storage.fetch_last_n_candles("AAPL", "1m", limit=100)
        
        elapsed = time.time() - start_time
        
        # Should fetch 100 times in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        
        print(f"Fetched 100 times in {elapsed:.2f} seconds")
        print(f"Rate: {100/elapsed:.2f} fetches/second")


class TestAggregatorPerformance:
    """Performance tests for aggregator"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_tick_aggregation_performance(self):
        """Test performance of tick aggregation."""
        aggregator = TickAggregator(flush_interval=60)
        
        num_ticks = 10000
        
        start_time = time.time()
        
        for i in range(num_ticks):
            tick = {
                "symbol": "AAPL",
                "ts_utc": f"2024-01-01T10:00:{i%60:02d}Z",
                "price": 150.0 + (i % 100) * 0.01,
                "qty": 100 + (i % 50)
            }
            await aggregator.aggregate_tick(tick)
        
        elapsed = time.time() - start_time
        
        # Should process 10000 ticks in reasonable time (< 5 seconds)
        assert elapsed < 5.0
        
        print(f"Processed {num_ticks} ticks in {elapsed:.2f} seconds")
        print(f"Rate: {num_ticks/elapsed:.2f} ticks/second")
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_multi_symbol_aggregation_performance(self):
        """Test performance of aggregating ticks for multiple symbols."""
        aggregator = TickAggregator(flush_interval=60)
        
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        num_ticks_per_symbol = 1000
        
        start_time = time.time()
        
        for symbol in symbols:
            for i in range(num_ticks_per_symbol):
                tick = {
                    "symbol": symbol,
                    "ts_utc": f"2024-01-01T10:00:{i%60:02d}Z",
                    "price": 150.0 + (i % 100) * 0.01,
                    "qty": 100 + (i % 50)
                }
                await aggregator.aggregate_tick(tick)
        
        elapsed = time.time() - start_time
        
        total_ticks = len(symbols) * num_ticks_per_symbol
        
        # Should process all ticks in reasonable time (< 10 seconds)
        assert elapsed < 10.0
        
        print(f"Processed {total_ticks} ticks for {len(symbols)} symbols in {elapsed:.2f} seconds")
        print(f"Rate: {total_ticks/elapsed:.2f} ticks/second")


class TestEndToEndPerformance:
    """End-to-end performance tests"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_full_pipeline_performance(self, storage):
        """Test performance of full ingestion pipeline."""
        config = {'rate_limit_per_minute': 100}
        adapter = YFinanceAdapter(config)
        
        # Mock adapter to avoid actual API calls
        mock_data = [
            {
                "symbol": "AAPL",
                "ts_utc": f"2024-01-01T10:{i//60:02d}:{i%60:02d}Z",
                "open": 150.0 + i * 0.01,
                "high": 151.0 + i * 0.01,
                "low": 149.0 + i * 0.01,
                "close": 150.5 + i * 0.01,
                "volume": 1000 + i,
                "provider": "yfinance"
            }
            for i in range(1000)
        ]
        
        with patch.object(adapter, 'fetch_historical_data', return_value=mock_data):
            start_time = time.time()
            
            # Fetch data
            data = await adapter.fetch_historical_data(
                symbol="AAPL",
                start="2024-01-01",
                end="2024-01-02",
                interval="1d"
            )
            
            # Store data
            for candle in data:
                await storage.insert_candle(candle)
            
            elapsed = time.time() - start_time
            
            # Should complete in reasonable time (< 5 seconds)
            assert elapsed < 5.0
            
            print(f"Full pipeline processed {len(data)} candles in {elapsed:.2f} seconds")
            print(f"Rate: {len(data)/elapsed:.2f} candles/second")


class TestConcurrentOperations:
    """Test concurrent operations performance"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_inserts(self, storage):
        """Test performance of concurrent insert operations."""
        num_tasks = 10
        candles_per_task = 100
        
        async def insert_candles(task_id):
            candles = [
                {
                    "symbol": f"SYMBOL{task_id}",
                    "ts_utc": f"2024-01-01T10:{i//60:02d}:{i%60:02d}Z",
                    "open": 150.0 + i * 0.01,
                    "high": 151.0 + i * 0.01,
                    "low": 149.0 + i * 0.01,
                    "close": 150.5 + i * 0.01,
                    "volume": 1000 + i,
                    "provider": "yfinance"
                }
                for i in range(candles_per_task)
            ]
            
            for candle in candles:
                await storage.insert_candle(candle)
        
        start_time = time.time()
        
        tasks = [insert_candles(i) for i in range(num_tasks)]
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        total_candles = num_tasks * candles_per_task
        
        # Should complete in reasonable time
        assert elapsed < 15.0
        
        print(f"Concurrently inserted {total_candles} candles in {elapsed:.2f} seconds")
        print(f"Rate: {total_candles/elapsed:.2f} candles/second")

