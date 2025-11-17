#!/usr/bin/env python3
"""
Standalone backfill script for historical market data.
Loads data from CSV files or fetches from adapters.
"""

import asyncio
import argparse
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.adapters.yfinance import YFinanceAdapter
from market_data_ingestion.adapters.alphavantage import AlphaVantageAdapter
from market_data_ingestion.src.logging_config import setup_logging
import logging
import tenacity

logger = logging.getLogger(__name__)

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    retry=tenacity.retry_if_exception_type(Exception),
    before_sleep=tenacity.before_sleep_log(logger, logging.WARNING)
)
async def backfill_symbols(symbols: List[str], period: str, interval: str, provider: str, storage: DataStorage):
    """Backfill data for given symbols."""
    total_processed = 0
    total_errors = 0

    # Determine end date (today)
    end_date = datetime.now().strftime('%Y-%m-%d')

    # Calculate start date based on period
    period_days = int(period.rstrip('d'))
    start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')

    # Choose adapter based on provider
    if provider == "yfinance":
        adapter = YFinanceAdapter({"rate_limit_per_minute": 100})
    elif provider == "alphavantage":
        adapter = AlphaVantageAdapter({
            "api_key": os.getenv("ALPHAVANTAGE_API_KEY", ""),
            "base_url": "https://www.alphavantage.co",
            "rate_limit_per_minute": 5
        })
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    for i, symbol in enumerate(symbols, 1):
        logger.info(f"[{i}/{len(symbols)}] Backfilling {symbol} from {start_date} to {end_date} with interval {interval}")

        try:
            data = await adapter.fetch_historical_data(symbol, start_date, end_date, interval)
            logger.info(f"Fetched {len(data)} records for {symbol}")

            # Store data
            for candle in data:
                await storage.insert_candle(candle)

            total_processed += 1

        except Exception as e:
            logger.error(f"Error backfilling {symbol}: {e}")
            total_errors += 1

    return total_processed, total_errors

def load_symbols_from_csv(csv_file: str) -> List[str]:
    """Load symbols from CSV file."""
    symbols = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'symbol' in row:
                    symbols.append(row['symbol'])
    except Exception as e:
        logger.error(f"Error loading symbols from CSV {csv_file}: {e}")
        raise
    return symbols

async def main():
    parser = argparse.ArgumentParser(description="Historical data backfill script")
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="List of symbols to backfill"
    )
    parser.add_argument(
        "--csv-file",
        help="CSV file containing symbols to backfill"
    )
    parser.add_argument(
        "--period",
        required=True,
        help="Period to backfill (e.g., 7d, 30d)"
    )
    parser.add_argument(
        "--interval",
        required=True,
        help="Interval to backfill (e.g., 1m, 1h, 1d)"
    )
    parser.add_argument(
        "--provider",
        default="yfinance",
        choices=["yfinance", "alphavantage"],
        help="Data provider to use"
    )
    parser.add_argument(
        "--db-url",
        help="Database URL",
        default=os.getenv("DATABASE_URL", "sqlite:///market_data.db")
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger.info(f"Starting backfill with symbols: {args.symbols}, period: {args.period}, interval: {args.interval}")

    # Determine symbols
    symbols = args.symbols or []
    if args.csv_file:
        symbols = load_symbols_from_csv(args.csv_file)
        logger.info(f"Loaded {len(symbols)} symbols from CSV file")

    if not symbols:
        logger.error("No symbols provided. Use --symbols or --csv-file")
        sys.exit(1)

    try:
        # Initialize storage
        storage = DataStorage(args.db_url)
        await storage.connect()
        await storage.create_tables()

        # Run backfill
        processed, errors = await backfill_symbols(symbols, args.period, args.interval, args.provider, storage)

        await storage.disconnect()
        logger.info(f"Backfill completed. Processed: {processed}, Errors: {errors}")

    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
