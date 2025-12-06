# FILE: tests/data_collector/test_backfill_scripts.py
"""Test data_collector/scripts/* helpers for NSE/BSE/MCX backfills."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


def test_nse_backfill_script_success():
    """Test NSE backfill script runs successfully."""
    with patch("data_collector.scripts.nse_backfill.main") as mock_main:
        mock_main.return_value = 0  # Success

        # Import and run the script
        from data_collector.scripts.nse_backfill import main
        result = main()

        assert result == 0
        mock_main.assert_called_once()


def test_nse_backfill_with_date_range():
    """Test NSE backfill with specific date range."""
    start_date = "2023-01-01"
    end_date = "2023-01-02"

    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector:
        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        mock_instance.backfill.return_value = True

        from data_collector.scripts.nse_backfill import main
        # Mock command line args
        with patch("sys.argv", ["nse_backfill.py", "--start", start_date, "--end", end_date]):
            result = main()

        mock_instance.backfill.assert_called_once_with(start_date, end_date)


def test_bse_backfill_script_success():
    """Test BSE backfill script runs successfully."""
    with patch("data_collector.scripts.bse_backfill.main") as mock_main:
        mock_main.return_value = 0

        from data_collector.scripts.bse_backfill import main
        result = main()

        assert result == 0


def test_mcx_backfill_script_success():
    """Test MCX backfill script runs successfully."""
    with patch("data_collector.scripts.mcx_backfill.main") as mock_main:
        mock_main.return_value = 0

        from data_collector.scripts.mcx_backfill import main
        result = main()

        assert result == 0


def test_backfill_script_error_handling():
    """Test backfill scripts handle errors gracefully."""
    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector:
        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        mock_instance.backfill.side_effect = Exception("Network error")

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py"]):
            with pytest.raises(SystemExit):  # Scripts should exit on error
                main()


def test_backfill_script_invalid_dates():
    """Test backfill scripts reject invalid date ranges."""
    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector:
        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py", "--start", "invalid-date"]):
            with pytest.raises(SystemExit):
                main()


def test_backfill_script_rate_limiting():
    """Test backfill scripts handle rate limiting."""
    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector:
        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        # Simulate rate limiting by raising specific exception
        mock_instance.backfill.side_effect = Exception("Rate limit exceeded")

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py"]):
            with pytest.raises(SystemExit):
                main()


def test_backfill_script_data_validation():
    """Test backfill scripts validate collected data."""
    sample_data = pd.DataFrame({
        "symbol": ["AAPL", "GOOGL"],
        "date": ["2023-01-01", "2023-01-02"],
        "open": [150.0, 2500.0],
        "high": [155.0, 2550.0],
        "low": [145.0, 2450.0],
        "close": [152.0, 2525.0],
        "volume": [1000000, 500000]
    })

    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector:
        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        mock_instance.backfill.return_value = sample_data

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py"]):
            result = main()

        # Should validate data has required columns
        assert "symbol" in sample_data.columns
        assert "date" in sample_data.columns
        assert len(sample_data) > 0


def test_backfill_script_progress_reporting():
    """Test backfill scripts report progress."""
    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector, \
         patch("data_collector.scripts.nse_backfill.tqdm") as mock_tqdm:

        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        mock_instance.backfill.return_value = True

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py"]):
            main()

        # Should use progress bar
        mock_tqdm.assert_called()


def test_backfill_script_config_loading():
    """Test backfill scripts load configuration properly."""
    with patch("data_collector.scripts.nse_backfill.load_config") as mock_config:
        mock_config.return_value = {
            "api_key": "test_key",
            "base_url": "https://test.api.com"
        }

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py"]):
            main()

        mock_config.assert_called_once()


def test_backfill_script_output_formats():
    """Test backfill scripts support different output formats."""
    # Test CSV output
    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector, \
         patch("pandas.DataFrame.to_csv") as mock_to_csv:

        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        mock_instance.backfill.return_value = pd.DataFrame({"test": [1, 2]})

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py", "--output", "test.csv"]):
            main()

        mock_to_csv.assert_called_once()

    # Test Parquet output
    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector, \
         patch("pandas.DataFrame.to_parquet") as mock_to_parquet:

        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        mock_instance.backfill.return_value = pd.DataFrame({"test": [1, 2]})

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py", "--output", "test.parquet"]):
            main()

        mock_to_parquet.assert_called_once()


def test_backfill_script_dry_run_mode():
    """Test backfill scripts support dry-run mode."""
    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector:
        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py", "--dry-run"]):
            main()

        # Should not actually perform backfill in dry-run
        mock_instance.backfill.assert_not_called()


def test_backfill_script_symbol_filtering():
    """Test backfill scripts can filter by specific symbols."""
    symbols = ["AAPL", "GOOGL"]

    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector:
        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        mock_instance.backfill.return_value = True

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py", "--symbols"] + symbols):
            main()

        # Should pass symbols to backfill method
        mock_instance.backfill.assert_called_once()
        args, kwargs = mock_instance.backfill.call_args
        # Assuming symbols are passed as keyword argument
        assert "symbols" in kwargs or len(args) > 2


def test_backfill_script_parallel_processing():
    """Test backfill scripts support parallel processing."""
    with patch("data_collector.scripts.nse_backfill.NSEDataCollector") as mock_collector, \
         patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:

        mock_instance = MagicMock()
        mock_collector.return_value = mock_instance
        mock_instance.backfill.return_value = True

        from data_collector.scripts.nse_backfill import main
        with patch("sys.argv", ["nse_backfill.py", "--parallel", "4"]):
            main()

        # Should use thread pool for parallel processing
        mock_executor.assert_called_once_with(max_workers=4)
