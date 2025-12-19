import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiosqlite
import asyncpg
import tenacity
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)


class DataStorage:
    def __init__(self, db_url: str = "sqlite:///market_data.db"):
        self.db_url = db_url
        self.db_type = self._get_db_type()
        self.conn = None
        self.pool = None  # For PostgreSQL connection pooling
        self.engine = None
        self.session_factory = None

    def _get_db_type(self) -> str:
        """Determine database type from URL."""
        parsed = urlparse(self.db_url)
        if parsed.scheme == 'postgresql':
            return 'postgresql'
        elif parsed.scheme == 'sqlite' or not parsed.scheme:
            return 'sqlite'
        else:
            raise ValueError(f"Unsupported database type: {parsed.scheme}")

    async def connect(self):
        """Connects to the database (SQLite or PostgreSQL)."""
        try:
            if self.db_type == 'sqlite':
                # SQLite connection
                db_path = self.db_url.replace('sqlite:///', '') if self.db_url.startswith('sqlite:///') else self.db_url
                self.conn = await aiosqlite.connect(db_path)
                logger.info(f"Connected to SQLite database: {db_path}")
            elif self.db_type == 'postgresql':
                # PostgreSQL connection with pooling
                self.pool = await asyncpg.create_pool(
                    self.db_url,
                    min_size=5,
                    max_size=20,
                    command_timeout=60
                )
                self.conn = await self.pool.acquire()
                logger.info(f"Connected to PostgreSQL database with connection pooling: {self.db_url}")
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
        except Exception as e:
            logger.error(f"Error connecting to {self.db_type} database: {e}")
            raise

    async def disconnect(self):
        """Disconnects from the database."""
        if self.engine:
            await self.engine.dispose()
            logger.info("SQLAlchemy engine disposed")

        if self.conn:
            if self.db_type == 'sqlite':
                await self.conn.close()
            elif self.db_type == 'postgresql':
                if self.pool:
                    await self.pool.release(self.conn)
                    await self.pool.close()
                else:
                    await self.conn.close()
            logger.info(f"Disconnected from {self.db_type} database")

    async def create_tables(self):
        """Creates the necessary tables in the database."""
        try:
            if self.db_type == 'sqlite':
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
                await self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ticks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol VARCHAR(40) NOT NULL,
                        ts_utc DATETIME NOT NULL,
                        price REAL NOT NULL,
                        volume REAL NOT NULL,
                        provider VARCHAR(50) NOT NULL,
                        raw_json TEXT,
                        UNIQUE(symbol, ts_utc, provider)
                    )
                    """
                )
                await self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dlq_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider VARCHAR(50) NOT NULL,
                        symbol VARCHAR(40),
                        error TEXT,
                        payload TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                await self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS order_book_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol VARCHAR(40) NOT NULL,
                        ts_utc DATETIME NOT NULL,
                        best_bid REAL,
                        best_ask REAL,
                        bids TEXT NOT NULL,
                        asks TEXT NOT NULL,
                        provider VARCHAR(50) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                await self.conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_order_book_symbol_ts ON order_book_snapshots(symbol, ts_utc DESC)"
                )
                await self.conn.commit()
            elif self.db_type == 'postgresql':
                await self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS candles (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        ts_utc TIMESTAMPTZ NOT NULL,
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
                await self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ticks (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(40) NOT NULL,
                        ts_utc TIMESTAMPTZ NOT NULL,
                        price REAL NOT NULL,
                        volume REAL NOT NULL,
                        provider VARCHAR(50) NOT NULL,
                        raw_json JSONB,
                        UNIQUE(symbol, ts_utc, provider)
                    )
                    """
                )
                await self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS dlq_events (
                        id SERIAL PRIMARY KEY,
                        provider VARCHAR(50) NOT NULL,
                        symbol VARCHAR(40),
                        error TEXT,
                        payload JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                await self.conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS order_book_snapshots (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(40) NOT NULL,
                        ts_utc TIMESTAMPTZ NOT NULL,
                        best_bid REAL,
                        best_ask REAL,
                        bids JSONB NOT NULL,
                        asks JSONB NOT NULL,
                        provider VARCHAR(50) NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                await self.conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_order_book_symbol_ts ON order_book_snapshots(symbol, ts_utc DESC)"
                )
            logger.info(f"Created tables in {self.db_type} database")
        except Exception as e:
            logger.error(f"Error creating tables in {self.db_type} database: {e}")
            raise

    async def insert_candle(self, candle: Dict[str, Any]):
        """Inserts a candle into the database."""
        try:
            if self.db_type == 'sqlite':
                await self.conn.execute(
                    """
                    INSERT OR IGNORE INTO candles (symbol, ts_utc, open, high, low, close, volume, provider)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (candle['symbol'], candle['ts_utc'], candle['open'], candle['high'],
                     candle['low'], candle['close'], candle['volume'], candle['provider']),
                )
                await self.conn.commit()
            elif self.db_type == 'postgresql':
                await self.conn.execute(
                    """
                    INSERT INTO candles (symbol, ts_utc, open, high, low, close, volume, provider)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (symbol, ts_utc, provider) DO NOTHING
                    """,
                    candle['symbol'], candle['ts_utc'], candle['open'], candle['high'],
                    candle['low'], candle['close'], candle['volume'], candle['provider']
                )
            logger.debug(f"Inserted candle: {candle}")
        except Exception as e:
            logger.error(f"Error inserting candle into {self.db_type} database: {e}")
            raise

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def insert_tick(self, tick: Dict[str, Any]):
        """Insert a normalized tick with retries for transient failures."""
        try:
            if self.db_type == 'sqlite':
                await self.conn.execute(
                    """
                    INSERT OR IGNORE INTO ticks (symbol, ts_utc, price, volume, provider, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (tick["symbol"], tick["ts_utc"], tick["price"], tick["volume"], tick["provider"], json.dumps(tick.get("raw", {}))),
                )
                await self.conn.commit()
            else:
                await self.conn.execute(
                    """
                    INSERT INTO ticks (symbol, ts_utc, price, volume, provider, raw_json)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (symbol, ts_utc, provider) DO NOTHING
                    """,
                    tick["symbol"],
                    tick["ts_utc"],
                    tick["price"],
                    tick["volume"],
                    tick["provider"],
                    json.dumps(tick.get("raw", {})),
                )
        except Exception as exc:
            logger.error(f"Error inserting tick: {exc}")
            raise

    async def insert_dlq(self, provider: str, symbol: Optional[str], error: str, payload: Dict[str, Any]):
        """Persist a DLQ record."""
        try:
            if self.db_type == 'sqlite':
                await self.conn.execute(
                    """
                    INSERT INTO dlq_events (provider, symbol, error, payload)
                    VALUES (?, ?, ?, ?)
                    """,
                    (provider, symbol, error, json.dumps(payload)),
                )
                await self.conn.commit()
            else:
                await self.conn.execute(
                    """
                    INSERT INTO dlq_events (provider, symbol, error, payload)
                    VALUES ($1, $2, $3, $4)
                    """,
                    provider,
                    symbol,
                    error,
                    json.dumps(payload),
                )
        except Exception as exc:
            logger.error(f"Error inserting DLQ event: {exc}")
            raise

    async def insert_order_book_snapshot(self, snapshot: Dict[str, Any]):
        """Persist an order book snapshot when depth data is available."""
        if not snapshot.get("bids") or not snapshot.get("asks"):
            return
        try:
            bids = snapshot["bids"]
            asks = snapshot["asks"]
            best_bid = snapshot.get("best_bid")
            best_ask = snapshot.get("best_ask")
            if self.db_type == 'sqlite':
                await self.conn.execute(
                    """
                    INSERT INTO order_book_snapshots (symbol, ts_utc, best_bid, best_ask, bids, asks, provider)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot["symbol"],
                        snapshot["ts_utc"],
                        best_bid,
                        best_ask,
                        json.dumps(bids),
                        json.dumps(asks),
                        snapshot["provider"],
                    ),
                )
                await self.conn.commit()
            else:
                await self.conn.execute(
                    """
                    INSERT INTO order_book_snapshots (symbol, ts_utc, best_bid, best_ask, bids, asks, provider)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    snapshot["symbol"],
                    snapshot["ts_utc"],
                    best_bid,
                    best_ask,
                    bids,
                    asks,
                    snapshot["provider"],
                )
        except Exception as exc:
            logger.error(f"Error inserting order book snapshot: {exc}")
            raise

    async def fetch_last_n_candles(self, symbol: str, interval: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches the last N candles for a symbol and interval."""
        try:
            if self.db_type == 'sqlite':
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
            elif self.db_type == 'postgresql':
                rows = await self.conn.fetch(
                    """
                    SELECT symbol, ts_utc, open, high, low, close, volume, provider
                    FROM candles
                    WHERE symbol = $1
                    ORDER BY ts_utc DESC
                    LIMIT $2
                    """,
                    symbol, limit
                )

            candles = [
                {
                    "symbol": row[0] if self.db_type == 'sqlite' else row['symbol'],
                    "ts_utc": row[1] if self.db_type == 'sqlite' else str(row['ts_utc']),
                    "open": row[2] if self.db_type == 'sqlite' else row['open'],
                    "high": row[3] if self.db_type == 'sqlite' else row['high'],
                    "low": row[4] if self.db_type == 'sqlite' else row['low'],
                    "close": row[5] if self.db_type == 'sqlite' else row['close'],
                    "volume": row[6] if self.db_type == 'sqlite' else row['volume'],
                    "provider": row[7] if self.db_type == 'sqlite' else row['provider'],
                }
                for row in rows
            ]
            return candles
        except Exception as e:
            logger.error(f"Error fetching last N candles from {self.db_type} database: {e}")
            return []

    async def health_check(self) -> bool:
        """Performs a health check on the database connection."""
        try:
            if self.db_type == 'sqlite':
                cursor = await self.conn.execute("SELECT 1")
                await cursor.fetchone()
                await cursor.close()
            elif self.db_type == 'postgresql':
                await self.conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def get_async_session(self):
        """Returns an async session factory for SQLAlchemy ORM operations."""
        if not self.session_factory:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.session_factory

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
