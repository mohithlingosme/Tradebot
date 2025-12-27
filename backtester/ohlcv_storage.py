"""
OHLCV Data Storage for Backtesting

Handles storage and retrieval of OHLCV candle data in Parquet format,
optimized for backtesting workloads.
"""

import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from common.market_data import Candle

logger = logging.getLogger(__name__)


class OHLCVStorage:
    """
    Storage for OHLCV candle data using Parquet format.

    Partitioned by symbol and date for optimal query performance.
    """

    def __init__(self, base_path: str = "data/ohlcv"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Define schema for OHLCV data
        self.schema = pa.schema([
            ('symbol', pa.string()),
            ('timestamp', pa.timestamp('ns')),
            ('open', pa.float64()),
            ('high', pa.float64()),
            ('low', pa.float64()),
            ('close', pa.float64()),
            ('volume', pa.float64()),
            ('timeframe', pa.string()),
            ('source', pa.string()),
        ])

    def _get_partition_path(self, symbol: str, date_obj: date, timeframe: str) -> Path:
        """Get partition path for symbol, date, and timeframe."""
        date_str = date_obj.strftime("%Y-%m-%d")
        return self.base_path / symbol / timeframe / f"{date_str}.parquet"

    def _ensure_partition_dir(self, symbol: str, timeframe: str) -> None:
        """Ensure partition directory exists."""
        (self.base_path / symbol / timeframe).mkdir(parents=True, exist_ok=True)

    def save_candles(self, candles: List[Candle], append: bool = True) -> None:
        """
        Save OHLCV candles to partitioned Parquet files.

        Args:
            candles: List of Candle objects
            append: Whether to append to existing data
        """
        if not candles:
            logger.warning("No candles provided")
            return

        # Group candles by symbol, timeframe, and date
        grouped: Dict[tuple, List[Candle]] = {}
        for candle in candles:
            date_obj = candle.timestamp.date()
            key = (candle.symbol, candle.timeframe, date_obj)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(candle)

        for (symbol, timeframe, date_obj), candle_list in grouped.items():
            partition_path = self._get_partition_path(symbol, date_obj, timeframe)
            self._ensure_partition_dir(symbol, timeframe)

            # Convert to DataFrame
            df = pd.DataFrame([{
                'symbol': c.symbol,
                'timestamp': c.timestamp,
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close,
                'volume': c.volume or 0.0,
                'timeframe': c.timeframe,
                'source': c.source or 'unknown'
            } for c in candle_list])

            if append and partition_path.exists():
                # Read existing and append
                try:
                    existing_df = pd.read_parquet(partition_path)
                    combined_df = pd.concat([existing_df, df], ignore_index=True)

                    # Remove duplicates based on timestamp
                    combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
                    combined_df = combined_df.sort_values('timestamp')

                except Exception as e:
                    logger.error(f"Error reading existing partition {partition_path}: {e}")
                    combined_df = df
            else:
                combined_df = df

            # Save to Parquet
            table = pa.Table.from_pandas(combined_df, schema=self.schema)
            pq.write_table(
                table,
                partition_path,
                compression='snappy',
                use_dictionary=True,
                row_group_size=50000
            )

            logger.info(f"Saved {len(candle_list)} candles for {symbol} {timeframe} on {date_obj}")

    def load_candles(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> List[Candle]:
        """
        Load OHLCV candles for a date range.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe (e.g., '1m', '1d')
            start_date: Start date YYYY-MM-DD
            end_date: End date YYYY-MM-DD

        Returns:
            List of Candle objects
        """
        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()

        symbol_path = self.base_path / symbol / timeframe
        if not symbol_path.exists():
            logger.warning(f"No data found for {symbol} {timeframe}")
            return []

        all_data = []
        current_date = start

        while current_date <= end:
            partition_path = self._get_partition_path(symbol, current_date, timeframe)

            if partition_path.exists():
                try:
                    df = pd.read_parquet(partition_path)
                    all_data.append(df)
                    logger.debug(f"Loaded {len(df)} candles for {symbol} {timeframe} on {current_date}")
                except Exception as e:
                    logger.error(f"Error reading partition {partition_path}: {e}")

            current_date = current_date + pd.Timedelta(days=1)

        if not all_data:
            logger.info(f"No data found for {symbol} {timeframe} between {start_date} and {end_date}")
            return []

        # Combine all data
        result_df = pd.concat(all_data, ignore_index=True)

        # Filter by exact date range
        result_df['timestamp'] = pd.to_datetime(result_df['timestamp'])
        mask = (result_df['timestamp'].dt.date >= start) & (result_df['timestamp'].dt.date <= end)
        result_df = result_df[mask]

        # Sort by timestamp
        result_df = result_df.sort_values('timestamp').reset_index(drop=True)

        # Convert back to Candle objects
        candles = []
        for _, row in result_df.iterrows():
            candles.append(Candle(
                symbol=row['symbol'],
                timestamp=row['timestamp'].to_pydatetime(),
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'] if pd.notna(row['volume']) else None,
                timeframe=row['timeframe'],
                source=row['source']
            ))

        logger.info(f"Loaded {len(candles)} total candles for {symbol} {timeframe} from {start_date} to {end_date}")
        return candles

    def get_available_symbols(self) -> List[str]:
        """Get list of symbols with available data."""
        if not self.base_path.exists():
            return []

        symbols = []
        for item in self.base_path.iterdir():
            if item.is_dir():
                symbols.append(item.name)

        return sorted(symbols)

    def get_available_timeframes(self, symbol: str) -> List[str]:
        """Get available timeframes for a symbol."""
        symbol_path = self.base_path / symbol
        if not symbol_path.exists():
            return []

        timeframes = []
        for item in symbol_path.iterdir():
            if item.is_dir():
                timeframes.append(item.name)

        return sorted(timeframes)

    def get_date_range(self, symbol: str, timeframe: str) -> Optional[tuple]:
        """Get available date range for a symbol and timeframe."""
        symbol_tf_path = self.base_path / symbol / timeframe
        if not symbol_tf_path.exists():
            return None

        dates = []
        for file_path in symbol_tf_path.glob("*.parquet"):
            try:
                date_str = file_path.stem
                date_obj = pd.to_datetime(date_str).date()
                dates.append(date_obj)
            except Exception as e:
                logger.warning(f"Invalid date format in filename {file_path}: {e}")

        if not dates:
            return None

        return min(dates), max(dates)

    def data_quality_check(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Perform data quality checks on stored data.

        Returns dict with quality metrics.
        """
        candles = self.load_candles(symbol, timeframe, start_date, end_date)

        if not candles:
            return {"status": "no_data"}

        issues = []
        timestamps = [c.timestamp for c in candles]

        # Check for duplicates
        if len(timestamps) != len(set(timestamps)):
            issues.append("duplicate_timestamps")

        # Check for missing candles (basic check for daily data)
        if timeframe == '1d':
            expected_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
            actual_days = len(set(c.timestamp.date() for c in candles))
            if actual_days < expected_days * 0.9:  # Allow 10% missing
                issues.append("missing_candles")

        # Check for outliers (price jumps > 20%)
        prices = [c.close for c in candles]
        if len(prices) > 1:
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            if any(abs(r) > 0.2 for r in returns):
                issues.append("price_outliers")

        # Check timezone alignment (should all be UTC)
        non_utc = [c for c in candles if c.timestamp.tzinfo != pd.Timestamp('2024-01-01').tz]
        if non_utc:
            issues.append("timezone_misalignment")

        return {
            "status": "ok" if not issues else "issues_found",
            "issues": issues,
            "candle_count": len(candles),
            "date_range": (min(timestamps), max(timestamps)) if timestamps else None
        }


# Data availability index
class DataAvailabilityIndex:
    """Index of available data for quick lookup."""

    def __init__(self, storage: OHLCVStorage):
        self.storage = storage
        self.index: Dict[str, Dict[str, tuple]] = {}  # symbol -> timeframe -> (start_date, end_date)

    def build_index(self) -> None:
        """Build the availability index."""
        symbols = self.storage.get_available_symbols()

        for symbol in symbols:
            self.index[symbol] = {}
            timeframes = self.storage.get_available_timeframes(symbol)

            for timeframe in timeframes:
                date_range = self.storage.get_date_range(symbol, timeframe)
                if date_range:
                    self.index[symbol][timeframe] = date_range

        logger.info(f"Built data availability index for {len(self.index)} symbols")

    def is_available(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> bool:
        """Check if data is available for the given parameters."""
        if symbol not in self.index or timeframe not in self.index[symbol]:
            return False

        start_avail, end_avail = self.index[symbol][timeframe]
        start_req = pd.to_datetime(start_date).date()
        end_req = pd.to_datetime(end_date).date()

        return start_req >= start_avail and end_req <= end_avail

    def get_coverage_report(self) -> Dict[str, Any]:
        """Generate a coverage report."""
        total_symbols = len(self.index)
        timeframes = set()
        date_ranges = []

        for symbol_data in self.index.values():
            timeframes.update(symbol_data.keys())
            for tf, (start, end) in symbol_data.items():
                date_ranges.append((start, end))

        if date_ranges:
            overall_start = min(d[0] for d in date_ranges)
            overall_end = max(d[1] for d in date_ranges)
        else:
            overall_start = overall_end = None

        return {
            "total_symbols": total_symbols,
            "available_timeframes": sorted(timeframes),
            "overall_date_range": (overall_start, overall_end) if overall_start else None
        }


# Example usage
if __name__ == "__main__":
    storage = OHLCVStorage()

    # Create sample candles
    from datetime import datetime, timezone
    import numpy as np

    timestamps = pd.date_range('2024-01-01 09:15:00', '2024-01-01 15:30:00', freq='1min')
    np.random.seed(42)

    sample_candles = []
    base_price = 150.0
    for ts in timestamps:
        price_change = np.random.normal(0, 0.5)
        open_price = base_price + price_change
        high_price = open_price + abs(np.random.normal(0, 0.2))
        low_price = open_price - abs(np.random.normal(0, 0.2))
        close_price = open_price + np.random.normal(0, 0.3)
        base_price = close_price

        sample_candles.append(Candle(
            symbol="RELIANCE",
            timestamp=ts.to_pydatetime().replace(tzinfo=timezone.utc),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=float(np.random.randint(1000, 10000)),
            timeframe="1m",
            source="sample"
        ))

    # Save sample data
    storage.save_candles(sample_candles)

    # Load data back
    loaded = storage.load_candles("RELIANCE", "1m", "2024-01-01", "2024-01-01")
    print(f"Loaded {len(loaded)} candles for RELIANCE")

    # Quality check
    quality = storage.data_quality_check("RELIANCE", "1m", "2024-01-01", "2024-01-01")
    print(f"Quality check: {quality}")

    print("OHLCV storage example completed successfully!")
