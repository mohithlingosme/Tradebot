"""
Unit tests for CLI commands
"""

import pytest
import asyncio
import os
import tempfile
import csv
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.cli import backfill, realtime, migrate, mock_server, load_symbols_from_csv
from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.adapters.yfinance import YFinanceAdapter
from market_data_ingestion.adapters.kite_ws import KiteWebSocketAdapter
from market_data_ingestion.core.aggregator import TickAggregator


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
def mock_config():
    """Mock configuration."""
    return {
        'database': {'db_path': 'sqlite:///test.db'},
        'providers': {
            'yfinance': {'rate_limit_per_minute': 100},
            'kite_ws': {
                'websocket_url': 'ws://localhost:8765',
                'api_key': 'test_key',
                'api_secret': 'test_secret'
            }
        }
    }


class TestBackfillCommand:
    """Test backfill CLI command"""
    
    @pytest.mark.asyncio
    async def test_backfill_with_symbols(self, temp_db, mock_config):
        """Test backfill command with symbols."""
        with patch('src.cli.yaml.safe_load', return_value=mock_config), \
             patch('src.cli.DataStorage') as mock_storage_class, \
             patch('src.cli.YFinanceAdapter') as mock_adapter_class:
            
            # Setup mocks
            mock_storage = AsyncMock()
            mock_storage_class.return_value = mock_storage
            
            mock_adapter = AsyncMock()
            mock_adapter.fetch_historical_data = AsyncMock(return_value=[
                {
                    "symbol": "AAPL",
                    "ts_utc": "2024-01-01T10:00:00Z",
                    "open": 150.0,
                    "high": 151.0,
                    "low": 149.0,
                    "close": 150.5,
                    "volume": 1000,
                    "provider": "yfinance"
                }
            ])
            mock_adapter_class.return_value = mock_adapter
            
            # Create args
            args = MagicMock()
            args.symbols = ["AAPL"]
            args.period = "7d"
            args.interval = "1d"
            args.csv_file = None
            
            # Run backfill
            await backfill(args)
            
            # Verify calls
            mock_storage.connect.assert_called_once()
            mock_storage.create_tables.assert_called_once()
            mock_adapter.fetch_historical_data.assert_called_once()
            mock_storage.insert_candle.assert_called()
            mock_storage.disconnect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_backfill_with_csv(self, temp_db, mock_config):
        """Test backfill command with CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['symbol'])
            writer.writeheader()
            writer.writerow({'symbol': 'AAPL'})
            writer.writerow({'symbol': 'GOOGL'})
            csv_path = f.name
        
        try:
            with patch('src.cli.yaml.safe_load', return_value=mock_config), \
                 patch('src.cli.DataStorage') as mock_storage_class, \
                 patch('src.cli.YFinanceAdapter') as mock_adapter_class:
                
                # Setup mocks
                mock_storage = AsyncMock()
                mock_storage_class.return_value = mock_storage
                
                mock_adapter = AsyncMock()
                mock_adapter.fetch_historical_data = AsyncMock(return_value=[])
                mock_adapter_class.return_value = mock_adapter
                
                # Create args
                args = MagicMock()
                args.symbols = None
                args.period = "7d"
                args.interval = "1d"
                args.csv_file = csv_path
                
                # Run backfill
                await backfill(args)
                
                # Verify adapter was called for both symbols
                assert mock_adapter.fetch_historical_data.call_count == 2
        finally:
            os.unlink(csv_path)
    
    @pytest.mark.asyncio
    async def test_backfill_no_symbols(self, mock_config):
        """Test backfill command without symbols."""
        with patch('src.cli.yaml.safe_load', return_value=mock_config):
            args = MagicMock()
            args.symbols = None
            args.csv_file = None
            args.period = "7d"
            args.interval = "1d"
            
            with pytest.raises(ValueError, match="No symbols provided"):
                await backfill(args)


class TestRealtimeCommand:
    """Test realtime CLI command"""
    
    @pytest.mark.asyncio
    async def test_realtime_with_mock_provider(self, temp_db, mock_config):
        """Test realtime command with mock provider."""
        with patch('src.cli.yaml.safe_load', return_value=mock_config), \
             patch('src.cli.DataStorage') as mock_storage_class, \
             patch('src.cli.TickAggregator') as mock_aggregator_class, \
             patch('src.cli.KiteWebSocketAdapter') as mock_adapter_class:
            
            # Setup mocks
            mock_storage = AsyncMock()
            mock_storage_class.return_value = mock_storage
            
            mock_aggregator = AsyncMock()
            mock_aggregator.run = AsyncMock()
            mock_aggregator.flush_candles = AsyncMock()
            mock_aggregator_class.return_value = mock_aggregator
            
            mock_adapter = AsyncMock()
            mock_adapter.__aenter__ = AsyncMock(return_value=mock_adapter)
            mock_adapter.__aexit__ = AsyncMock(return_value=None)
            mock_adapter.realtime_connect = AsyncMock()
            mock_adapter_class.return_value = mock_adapter
            
            # Create args
            args = MagicMock()
            args.symbols = ["AAPL"]
            args.provider = "mock"
            
            # Run realtime (with timeout to prevent hanging)
            try:
                await asyncio.wait_for(realtime(args), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            
            # Verify initialization
            mock_storage.connect.assert_called_once()
            mock_storage.create_tables.assert_called_once()


class TestMigrateCommand:
    """Test migrate CLI command"""
    
    @pytest.mark.asyncio
    async def test_migrate_success(self, temp_db, mock_config):
        """Test migrate command."""
        with patch('src.cli.yaml.safe_load', return_value=mock_config), \
             patch('src.cli.DataStorage') as mock_storage_class:
            
            # Setup mocks
            mock_storage = AsyncMock()
            mock_storage_class.return_value = mock_storage
            
            # Create args
            args = MagicMock()
            
            # Run migrate
            await migrate(args)
            
            # Verify calls
            mock_storage.connect.assert_called_once()
            mock_storage.create_tables.assert_called_once()
            mock_storage.disconnect.assert_called_once()


class TestLoadSymbolsFromCSV:
    """Test load_symbols_from_csv function"""
    
    def test_load_symbols_from_csv_success(self):
        """Test loading symbols from CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['symbol'])
            writer.writeheader()
            writer.writerow({'symbol': 'AAPL'})
            writer.writerow({'symbol': 'GOOGL'})
            writer.writerow({'symbol': 'MSFT'})
            csv_path = f.name
        
        try:
            symbols = load_symbols_from_csv(csv_path)
            assert len(symbols) == 3
            assert 'AAPL' in symbols
            assert 'GOOGL' in symbols
            assert 'MSFT' in symbols
        finally:
            os.unlink(csv_path)
    
    def test_load_symbols_from_csv_invalid_file(self):
        """Test loading symbols from non-existent CSV file."""
        with pytest.raises(FileNotFoundError):
            load_symbols_from_csv('nonexistent.csv')
    
    def test_load_symbols_from_csv_empty_file(self):
        """Test loading symbols from empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['symbol'])
            writer.writeheader()
            csv_path = f.name
        
        try:
            symbols = load_symbols_from_csv(csv_path)
            assert len(symbols) == 0
        finally:
            os.unlink(csv_path)

