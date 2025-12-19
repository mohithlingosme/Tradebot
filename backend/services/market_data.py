from __future__ import annotations

from typing import List

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import MarketCandle, OrderBookSnapshot


async def fetch_recent_candles(session: AsyncSession, symbol: str, limit: int = 720) -> List[MarketCandle]:
    stmt: Select[MarketCandle] = (
        select(MarketCandle)
        .where(MarketCandle.symbol == symbol.upper())
        .order_by(MarketCandle.ts_utc.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    candles = list(result.scalars().all())
    candles.reverse()
    return candles


async def fetch_order_book_history(
    session: AsyncSession, symbol: str, limit: int = 50
) -> List[OrderBookSnapshot]:
    stmt: Select[OrderBookSnapshot] = (
        select(OrderBookSnapshot)
        .where(OrderBookSnapshot.symbol == symbol.upper())
        .order_by(OrderBookSnapshot.ts_utc.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    snapshots = list(result.scalars().all())
    snapshots.reverse()
    return snapshots
