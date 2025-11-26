from __future__ import annotations

"""
Async PostgreSQL helper with schema bootstrap for Phase 3 ingestion.
"""

import logging
from asyncio import AbstractEventLoop, get_event_loop
from pathlib import Path
from typing import Any, AsyncIterator, Iterable, Optional

import asyncpg

logger = logging.getLogger(__name__)


class NotConnectedError(RuntimeError):
    """Raised when DB operations are attempted without an active connection pool."""


class PostgresClient:
    """
    Thin async wrapper around asyncpg with a couple of convenience helpers.
    """

    def __init__(
        self,
        dsn: str,
        min_size: int = 1,
        max_size: int = 10,
        loop: Optional[AbstractEventLoop] = None,
    ):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None
        self.loop = loop or get_event_loop()

    async def __aenter__(self) -> "PostgresClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def connect(self) -> None:
        """Initialize the connection pool."""
        if self.pool:
            return

        self.pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            timeout=30,
        )
        logger.info("Connected to database")

    async def close(self) -> None:
        """Close the pool gracefully."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection closed")

    def _ensure_pool(self) -> asyncpg.Pool:
        if not self.pool:
            raise NotConnectedError("Call connect() before executing queries")
        return self.pool

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args) -> str:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, params: Iterable[Iterable[Any]]) -> None:
        pool = self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.executemany(query, params)

    async def run_schema(self, schema_sql: str) -> None:
        """
        Execute a multi-statement SQL payload (DDL).
        """
        pool = self._ensure_pool()
        statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
        async with pool.acquire() as conn:
            async with conn.transaction():
                for stmt in statements:
                    await conn.execute(stmt)

    async def ensure_phase3_schema(self, schema_path: Optional[Path] = None) -> None:
        """
        Ensure the Phase 3 tables exist by applying the bundled SQL file.
        """
        if schema_path is None:
            schema_path = (
                Path(__file__).resolve().parents[1]
                / "database"
                / "schemas"
                / "phase3_market_intelligence.sql"
            )

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        schema_sql = schema_path.read_text(encoding="utf-8")
        await self.run_schema(schema_sql)

