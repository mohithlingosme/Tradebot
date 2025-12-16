"""
High-Performance Parquet Storage for Financial Tick Data

This module provides efficient storage and retrieval of high-frequency market data
using Apache Parquet format with optimized partitioning for algorithmic trading.

Author: BLACKBOXAI
"""

import os
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime, date

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


class ParquetStorage:
    """
    High-performance Parquet storage for financial tick data.

    Features:
    - Partitioned storage by symbol and date for optimal query performance
    - Efficient append operations for high-frequency data
    - Snappy compression for disk space optimization
    - Range queries for historical data loading
    - CSV ingestion utility for legacy data

    Schema:
    - timestamp: datetime64[ns] - Trade timestamp
    - price: float64 - Trade price
    - volume: int64 - Trade volume
    """

    def __init__(self, base_path: str = "data/history"):
        """
        Initialize Parquet storage.

        Args:
            base_path: Base directory for storing Parquet files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Define the expected schema
        self.schema = pa.schema([
            ('timestamp', pa.timestamp('ns')),
            ('price', pa.float64()),
            ('volume', pa.int64())
        ])

        logger.info(f"Initialized ParquetStorage with base path: {self.base_path}")

    def _get_partition_path(self, symbol: str, date_obj: date) -> Path:
        """
        Get the partition path for a given symbol and date.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            date_obj: Date object

        Returns:
            Path to the partition file
        """
        date_str = date_obj.strftime("%Y-%m-%d")
        return self.base_path / symbol / f"{date_str}.parquet"

    def _ensure_partition_dir(self, symbol: str) -> None:
        """Ensure the partition directory exists for a symbol."""
        (self.base_path / symbol).mkdir(parents=True, exist_ok=True)

    def save_ticks(self, symbol: str, data: pd.DataFrame, append: bool = True) -> None:
        """
        Save tick data to partitioned Parquet files.

        Args:
            symbol: Stock symbol
            data: DataFrame with columns [timestamp, price, volume]
            append: If True, append to existing data; if False, overwrite
        """
        if data.empty:
            logger.warning(f"No data provided for symbol {symbol}")
            return

        # Validate required columns
        required_cols = ['timestamp', 'price', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Ensure timestamp is datetime
        data = data.copy()
        data['timestamp'] = pd.to_datetime(data['timestamp'])

        # Group data by date for partitioning
        data['date'] = data['timestamp'].dt.date
        grouped = data.groupby('date')

        for date_val, group in grouped:
            # Remove the date column before saving
            group = group.drop('date', axis=1)

            partition_path = self._get_partition_path(symbol, date_val)
            self._ensure_partition_dir(symbol)

            if append and partition_path.exists():
                # Read existing data and append
                try:
                    existing_df = pd.read_parquet(partition_path)
                    combined_df = pd.concat([existing_df, group], ignore_index=True)

                    # Remove duplicates based on timestamp (keep latest)
                    combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
                    combined_df = combined_df.sort_values('timestamp')

                except Exception as e:
                    logger.error(f"Error reading existing partition {partition_path}: {e}")
                    combined_df = group
            else:
                combined_df = group

            # Save to Parquet with Snappy compression
            table = pa.Table.from_pandas(combined_df, schema=self.schema)
            pq.write_table(
                table,
                partition_path,
                compression='snappy',
                use_dictionary=True,
                row_group_size=50000  # Optimize for query performance
            )

            logger.info(f"Saved {len(group)} ticks for {symbol} on {date_val}")

    def load_history(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Load historical tick data for a date range.

        Args:
            symbol: Stock symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with tick data for the date range
        """
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()

        symbol_path = self.base_path / symbol
        if not symbol_path.exists():
            logger.warning(f"No data found for symbol {symbol}")
            return pd.DataFrame(columns=['timestamp', 'price', 'volume'])

        all_data = []
        current_date = start

        while current_date <= end:
            partition_path = self._get_partition_path(symbol, current_date)

            if partition_path.exists():
                try:
                    df = pd.read_parquet(partition_path)
                    all_data.append(df)
                    logger.debug(f"Loaded {len(df)} ticks for {symbol} on {current_date}")
                except Exception as e:
                    logger.error(f"Error reading partition {partition_path}: {e}")

            current_date = current_date + pd.Timedelta(days=1)

        if not all_data:
            logger.info(f"No data found for {symbol} between {start_date} and {end_date}")
            return pd.DataFrame(columns=['timestamp', 'price', 'volume'])

        # Combine all data
        result_df = pd.concat(all_data, ignore_index=True)

        # Filter by exact date range (in case of timezone issues)
        result_df['timestamp'] = pd.to_datetime(result_df['timestamp'])
        mask = (result_df['timestamp'].dt.date >= start) & (result_df['timestamp'].dt.date <= end)
        result_df = result_df[mask]

        # Sort by timestamp
        result_df = result_df.sort_values('timestamp').reset_index(drop=True)

        logger.info(f"Loaded {len(result_df)} total ticks for {symbol} from {start_date} to {end_date}")
        return result_df

    def convert_csv_to_parquet(self, csv_path: str, symbol: str,
                              date_column: str = 'timestamp',
                              price_column: str = 'price',
                              volume_column: str = 'volume',
                              date_format: Optional[str] = None) -> None:
        """
        Convert CSV file to Parquet format.

        Args:
            csv_path: Path to CSV file
            symbol: Stock symbol
            date_column: Name of date/timestamp column
            price_column: Name of price column
            volume_column: Name of volume column
            date_format: Date format string if needed for parsing
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info(f"Converting CSV {csv_path} to Parquet for symbol {symbol}")

        # Read CSV with appropriate parsing
        dtype_mapping = {price_column: 'float64', volume_column: 'int64'}

        df = pd.read_csv(csv_path, dtype=dtype_mapping)

        # Rename columns to standard schema
        column_mapping = {
            date_column: 'timestamp',
            price_column: 'price',
            volume_column: 'volume'
        }
        df = df.rename(columns=column_mapping)

        # Parse timestamp
        if date_format:
            df['timestamp'] = pd.to_datetime(df['timestamp'], format=date_format)
        else:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Ensure we have the required columns
        required_cols = ['timestamp', 'price', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV must contain columns that map to: {required_cols}")

        # Select only required columns
        df = df[required_cols]

        # Save to Parquet
        self.save_ticks(symbol, df, append=True)

        logger.info(f"Successfully converted {len(df)} rows from CSV to Parquet")

    def get_available_symbols(self) -> List[str]:
        """Get list of symbols with available data."""
        if not self.base_path.exists():
            return []

        symbols = []
        for item in self.base_path.iterdir():
            if item.is_dir():
                symbols.append(item.name)

        return sorted(symbols)

    def get_date_range(self, symbol: str) -> Optional[tuple]:
        """
        Get the available date range for a symbol.

        Returns:
            Tuple of (start_date, end_date) or None if no data
        """
        symbol_path = self.base_path / symbol
        if not symbol_path.exists():
            return None

        dates = []
        for file_path in symbol_path.glob("*.parquet"):
            try:
                date_str = file_path.stem  # filename without extension
                date_obj = pd.to_datetime(date_str).date()
                dates.append(date_obj)
            except Exception as e:
                logger.warning(f"Invalid date format in filename {file_path}: {e}")

        if not dates:
            return None

        return min(dates), max(dates)

    def cleanup_old_data(self, symbol: str, days_to_keep: int) -> int:
        """
        Remove data older than specified days for a symbol.

        Args:
            symbol: Stock symbol
            days_to_keep: Number of days of data to retain

        Returns:
            Number of files removed
        """
        symbol_path = self.base_path / symbol
        if not symbol_path.exists():
            return 0

        cutoff_date = pd.Timestamp.now().date() - pd.Timedelta(days=days_to_keep)
        removed_count = 0

        for file_path in symbol_path.glob("*.parquet"):
            try:
                date_str = file_path.stem
                file_date = pd.to_datetime(date_str).date()

                if file_date < cutoff_date:
                    file_path.unlink()
                    removed_count += 1
                    logger.info(f"Removed old data file: {file_path}")

            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")

        return removed_count


# Example usage
if __name__ == "__main__":
    # Initialize storage
    storage = ParquetStorage()

    # Create dummy tick data
    import numpy as np

    timestamps = pd.date_range('2024-01-01 09:30:00', '2024-01-01 16:00:00', freq='1s')
    np.random.seed(42)

    dummy_data = pd.DataFrame({
        'timestamp': timestamps,
        'price': 150.0 + np.random.normal(0, 2, len(timestamps)),  # AAPL-like price
        'volume': np.random.randint(1, 1000, len(timestamps))
    })

    # Save the data
    storage.save_ticks('AAPL', dummy_data)

    # Load data back
    loaded_data = storage.load_history('AAPL', '2024-01-01', '2024-01-01')
    print(f"Loaded {len(loaded_data)} ticks for AAPL")
    print(loaded_data.head())

    print("Parquet storage example completed successfully!")
