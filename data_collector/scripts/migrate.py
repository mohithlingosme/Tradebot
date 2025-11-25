#!/usr/bin/env python3
"""
Standalone migration script for market data ingestion database.
Supports both SQLite and PostgreSQL databases.
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add the project root to the Python path
ROOT_PATH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_PATH))

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="Database migration script")
    parser.add_argument(
        "--db-url",
        help="Database URL (e.g., sqlite:///market_data.db or postgresql://user:pass@localhost:5432/market_data)",
        default=os.getenv("DATABASE_URL", "sqlite:///market_data.db")
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if tables exist"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger.info(f"Starting database migration with URL: {args.db_url}")

    try:
        # Initialize storage
        storage = DataStorage(args.db_url)

        # Connect to database
        await storage.connect()
        logger.info("Connected to database successfully")

        # Create tables
        await storage.create_tables()
        logger.info("Database migration completed successfully")

        # Disconnect
        await storage.disconnect()
        logger.info("Disconnected from database")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
