from __future__ import annotations

"""Shared ingestion interfaces and helpers."""

from typing import Any, List, Protocol

from sqlmodel import Session

from common.market_data import Candle

try:
    from backend.app.database import engine
    from backend.app.models import Candle as DBCandle
except Exception:  # pragma: no cover - optional at import time
    engine = None
    DBCandle = None


class BaseIngestor(Protocol):
    """Protocol for ingestion flows."""

    def fetch_raw(self, symbol: str, **kwargs: Any) -> Any:
        ...

    def normalize(self, raw: Any) -> List[Candle]:
        ...

    def save(self, candles: List[Candle]) -> int:
        ...


def save_candles_to_db(candles: List[Candle], session: Session | None = None) -> int:
    """
    Persist normalized candles into the SQLModel-backed database.

    Returns the number of records saved.
    """
    if not candles:
        return 0
    if engine is None or DBCandle is None:
        raise RuntimeError("Database engine is not available for saving candles.")

    owns_session = session is None
    session = session or Session(engine)

    try:
        for candle in candles:
            db_row = DBCandle(
                symbol=candle.symbol,
                timestamp=candle.timestamp,
                open=candle.open,
                high=candle.high,
                low=candle.low,
                close=candle.close,
                volume=int(candle.volume or 0),
                provider=candle.source or "unknown",
            )
            session.add(db_row)
        session.commit()
        return len(candles)
    finally:
        if owns_session:
            session.close()

