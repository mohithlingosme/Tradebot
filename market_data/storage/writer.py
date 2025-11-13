"""
Async storage layer for market data using asyncpg.
"""

import asyncio
import logging
from typing import List, Optional
from uuid import UUID

import asyncpg

from ..normalization.models import Trade, Quote, Candle

logger = logging.getLogger(__name__)


class DataWriter:
    """Async data writer for market data."""

    def __init__(self, dsn: str, min_connections: int = 1, max_connections: int = 10):
        self.dsn = dsn
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        """Connect to the database."""
        try:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=60
            )
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the database."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from database")

    async def write_trades(self, trades: List[Trade]) -> int:
        """Write trades to database with upsert."""
        if not self.pool:
            raise RuntimeError("Not connected to database")

        if not trades:
            return 0

        query = """
        INSERT INTO trades (
            provider_id, instrument_id, trade_id, price, size, side,
            event_time, received_at, ingest_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (instrument_id, event_time, trade_id)
        DO NOTHING
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                count = 0
                for trade in trades:
                    try:
                        await conn.execute(
                            query,
                            trade.provider_id,
                            trade.instrument_id,
                            trade.trade_id,
                            trade.price,
                            trade.size,
                            trade.side,
                            trade.event_time,
                            trade.received_at,
                            trade.ingest_id
                        )
                        count += 1
                    except Exception as e:
                        logger.warning(f"Failed to write trade {trade}: {e}")

                return count

    async def write_quotes(self, quotes: List[Quote]) -> int:
        """Write quotes to database with upsert."""
        if not self.pool:
            raise RuntimeError("Not connected to database")

        if not quotes:
            return 0

        query = """
        INSERT INTO quotes (
            provider_id, instrument_id, bid_price, bid_size, ask_price, ask_size,
            last_price, last_size, event_time, received_at, ingest_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (provider_id, instrument_id)
        DO UPDATE SET
            bid_price = EXCLUDED.bid_price,
            bid_size = EXCLUDED.bid_size,
            ask_price = EXCLUDED.ask_price,
            ask_size = EXCLUDED.ask_size,
            last_price = EXCLUDED.last_price,
            last_size = EXCLUDED.last_size,
            event_time = EXCLUDED.event_time,
            received_at = EXCLUDED.received_at,
            ingest_id = EXCLUDED.ingest_id
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                count = 0
                for quote in quotes:
                    try:
                        await conn.execute(
                            query,
                            quote.provider_id,
                            quote.instrument_id,
                            quote.bid_price,
                            quote.bid_size,
                            quote.ask_price,
                            quote.ask_size,
                            quote.last_price,
                            quote.last_size,
                            quote.event_time,
                            quote.received_at,
                            quote.ingest_id
                        )
                        count += 1
                    except Exception as e:
                        logger.warning(f"Failed to write quote {quote}: {e}")

                return count

    async def write_candles(self, candles: List[Candle]) -> int:
        """Write candles to database with upsert."""
        if not self.pool:
            raise RuntimeError("Not connected to database")

        if not candles:
            return 0

        query = """
        INSERT INTO candles (
            provider_id, instrument_id, granularity, bucket_start, open_price,
            high_price, low_price, close_price, volume, event_time, received_at, ingest_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (provider_id, instrument_id, granularity, bucket_start)
        DO UPDATE SET
            open_price = EXCLUDED.open_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume,
            event_time = EXCLUDED.event_time,
            received_at = EXCLUDED.received_at,
            ingest_id = EXCLUDED.ingest_id
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                count = 0
                for candle in candles:
                    try:
                        await conn.execute(
                            query,
                            candle.provider_id,
                            candle.instrument_id,
                            candle.granularity,
                            candle.bucket_start,
                            candle.open_price,
                            candle.high_price,
                            candle.low_price,
                            candle.close_price,
                            candle.volume,
                            candle.event_time,
                            candle.received_at,
                            candle.ingest_id
                        )
                        count += 1
                    except Exception as e:
                        logger.warning(f"Failed to write candle {candle}: {e}")

                return count

    async def write_raw_trades(self, provider_id: int, instrument_id: int,
                              raw_trades: List[Dict]) -> int:
        """Write raw trades to trades_raw table."""
        if not self.pool:
            raise RuntimeError("Not connected to database")

        if not raw_trades:
            return 0

        query = """
        INSERT INTO trades_raw (provider_id, instrument_id, event_time, payload)
        VALUES ($1, $2, $3, $4)
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                count = 0
                for raw_trade in raw_trades:
                    try:
                        await conn.execute(
                            query,
                            provider_id,
                            instrument_id,
                            raw_trade.get("event_time"),
                            raw_trade
                        )
                        count += 1
                    except Exception as e:
                        logger.warning(f"Failed to write raw trade: {e}")

                return count

    async def get_provider_id(self, provider_name: str) -> Optional[int]:
        """Get provider ID by name."""
        if not self.pool:
            raise RuntimeError("Not connected to database")

        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT id FROM providers WHERE name = $1",
                provider_name
            )

    async def get_instrument_id(self, symbol: str) -> Optional[int]:
        """Get instrument ID by symbol."""
        if not self.pool:
            raise RuntimeError("Not connected to database")

        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT id FROM instruments WHERE symbol = $1",
                symbol
            )
