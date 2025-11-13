import asyncio
import logging
from typing import Dict, Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class DataStorage:
    def __init__(self, db_path: str = "market_data.db"):
        self.db_path = db_path
        self.conn = None

    async def connect(self):
        """Connects to the SQLite database."""
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            logger.info(f"Connected to SQLite database: {self.db_path}")
        except Exception as e:
            logger.error(f"Error connecting to SQLite database: {e}")
            raise

    async def disconnect(self):
        """Disconnects from the SQLite database."""
        if self.conn:
            await self.conn.close()
            logger.info("Disconnected from SQLite database")

    async def create_tables(self):
        """Creates the necessary tables in the database."""
        try:
            await self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS candles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(20) NOT NULL,
                    ts_utc DATETIME NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume REAL NOT NULL,
                    provider VARCHAR(50) NOT NULL,
                    UNIQUE(symbol, ts_utc, provider)
                )
                """
            )
            await self.conn.commit()
            logger.info("Created tables in SQLite database")
        except Exception as e:
            logger.error(f"Error creating tables in SQLite database: {e}")
            raise

    async def insert_candle(self, candle: Dict[str, Any]):
        """Inserts a candle into the database."""
        try:
            await self.conn.execute(
                """
                INSERT OR IGNORE INTO candles (symbol, ts_utc, open, high, low, close, volume, provider)
                VALUES (:symbol, :ts_utc, :open, :high, :low, :close, :volume, :provider)
                """,
                candle,
            )
            await self.conn.commit()
            logger.debug(f"Inserted candle: {candle}")
        except Exception as e:
            logger.error(f"Error inserting candle into SQLite database: {e}")

    async def fetch_last_n_candles(self, symbol: str, interval: str, limit: int = 50) -> list[Dict[str, Any]]:
        """Fetches the last N candles for a symbol and interval."""
        try:
            cursor = await self.conn.execute(
                """
                SELECT symbol, ts_utc, open, high, low, close, volume, provider
                FROM candles
                WHERE symbol = ?
                ORDER BY ts_utc DESC
                LIMIT ?
                """,
                (symbol, limit),
            )
            rows = await cursor.fetchall()
            await cursor.close()

            candles = [
                {
                    "symbol": row[0],
                    "ts_utc": row[1],
                    "open": row[2],
                    "high": row[3],
                    "low": row[4],
                    "close": row[5],
                    "volume": row[6],
                    "provider": row[7],
                }
                for row in rows
            ]
            return candles
        except Exception as e:
            logger.error(f"Error fetching last N candles from SQLite database: {e}")
            return []

async def main():
    # Example usage:
    logging.basicConfig(level=logging.DEBUG)
    storage = DataStorage()
    await storage.connect()
    await storage.create_tables()

    candle = {
        "symbol": "RELIANCE.NS",
        "ts_utc": "2024-01-01T10:00:00Z",
        "open": 2500.0,
        "high": 2501.0,
        "low": 2499.0,
        "close": 2500.5,
        "volume": 100,
        "provider": "yfinance",
    }
    await storage.insert_candle(candle)

    candles = await storage.fetch_last_n_candles("RELIANCE.NS", "1m", limit=10)
    logger.info(f"Last 10 candles: {candles}")

    await storage.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
