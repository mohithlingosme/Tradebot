from __future__ import annotations

"""
Canonical candle model and normalization helpers.

Timestamps are normalized to timezone-aware UTC datetimes to avoid ambiguity
across ingestion pipelines.
"""

from datetime import datetime, timezone
from typing import Any, Iterable, List, Mapping, Sequence

from pydantic import BaseModel, Field, field_validator


class Candle(BaseModel):
    """Normalized OHLCV candle representation."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None
    source: str | None = None
    timeframe: str = Field(default="1m", pattern=r"^\d+[smhdw]$")

    @field_validator("timestamp")
    @classmethod
    def _ensure_tzinfo(cls, value: datetime) -> datetime:
        """Force all timestamps to UTC to keep ingestion consistent."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def _coerce_timestamp(raw_value: Any) -> datetime:
    if isinstance(raw_value, datetime):
        return raw_value
    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(raw_value, tz=timezone.utc)
    if isinstance(raw_value, str):
        cleaned = raw_value.rstrip("Z")
        try:
            parsed = datetime.fromisoformat(cleaned)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError as exc:
            raise ValueError(f"Unrecognized timestamp format: {raw_value}") from exc
    raise ValueError(f"Unsupported timestamp type: {type(raw_value)}")


def _extract_numeric(record: Mapping[str, Any], *keys: str) -> float:
    for key in keys:
        if key in record and record[key] is not None:
            return float(record[key])
    raise ValueError(f"Missing required numeric fields {keys} in record {record}")


def _iter_rows(raw: Any) -> Iterable[Mapping[str, Any]]:
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        if "records" in raw:
            return raw["records"] or []
        if "candles" in raw:
            return raw["candles"] or []
        return [raw]
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        return raw

    try:
        import pandas as pd  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        pd = None

    if pd is not None and isinstance(raw, pd.DataFrame):
        return raw.to_dict(orient="records")
    raise ValueError(f"Unsupported raw payload type: {type(raw)}")


def normalize_to_candles(raw: Any, symbol: str, timeframe: str, source: str) -> List[Candle]:
    """
    Convert provider-specific payloads into a list of normalized Candle objects.

    - Enforces UTC timestamps
    - Filters out any candles that land in the future
    - Ensures ascending order by timestamp
    - Validates presence of OHLC fields
    """
    candles: List[Candle] = []

    now_utc = datetime.now(timezone.utc)

    for record in _iter_rows(raw):
        ts_value = (
            record.get("timestamp")
            or record.get("time")
            or record.get("datetime")
            or record.get("date")
            or record.get("ts_utc")
        )
        if ts_value is None:
            raise ValueError(f"Record missing timestamp: {record}")

        timestamp = _coerce_timestamp(ts_value)

        open_price = _extract_numeric(record, "open", "o", "Open")
        high_price = _extract_numeric(record, "high", "h", "High")
        low_price = _extract_numeric(record, "low", "l", "Low")
        close_price = _extract_numeric(record, "close", "c", "Close")
        volume = record.get("volume") or record.get("v") or record.get("Volume")

        if timestamp > now_utc:
            continue

        candles.append(
            Candle(
                symbol=symbol,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=float(volume) if volume is not None else None,
                source=source,
                timeframe=timeframe,
            )
        )

    candles.sort(key=lambda candle: candle.timestamp)
    return candles
