from __future__ import annotations

"""Commodity market data ingestion."""

from datetime import datetime, timedelta
from typing import Any, List, Mapping, Sequence

from backend.data_ingestion.data_fetcher import DataFetcher

from common.market_data import Candle, normalize_to_candles
from ingestion.base import BaseIngestor, save_candles_to_db


class CommodityIngestor(BaseIngestor):
    """Fetch and store commodity candles (e.g., energy, metals)."""

    def __init__(
        self,
        timeframe: str = "1h",
        source: str = "yfinance",
        fetcher: DataFetcher | None = None,
    ) -> None:
        self.timeframe = timeframe
        self.source = source
        self.fetcher = fetcher or DataFetcher(
            {"data_sources": [{"name": source, "type": source, "enabled": True}]}
        )
        self._last_symbol: str | None = None

    def fetch_raw(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        **kwargs: Any,
    ) -> Any:
        """Fetch raw commodity candles."""
        self._last_symbol = symbol
        if "raw" in kwargs:
            return kwargs["raw"]

        start = start or datetime.utcnow() - timedelta(days=30)
        end = end or datetime.utcnow()
        return self.fetcher.fetch_historical_data(symbol, start, end, interval=self.timeframe)

    def _resolve_symbol(self, raw: Any, records: Sequence[Mapping[str, Any]]) -> str:
        symbol = None
        if isinstance(raw, Mapping):
            symbol = raw.get("symbol")
        if not symbol and records:
            first = records[0]
            if isinstance(first, Mapping) and "symbol" in first:
                symbol = first["symbol"]
        return (symbol or self._last_symbol or "").upper()

    def normalize(self, raw: Any) -> List[Candle]:
        """Normalize provider payloads to candles."""
        records: Sequence[Mapping[str, Any]] = []
        if isinstance(raw, Mapping) and "records" in raw:
            records = raw.get("records") or []
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            records = raw

        symbol = self._resolve_symbol(raw, records)
        if not symbol:
            raise ValueError("Symbol required to normalize commodity data")

        return normalize_to_candles(records, symbol=symbol, timeframe=self.timeframe, source=self.source)

    def save(self, candles: List[Candle]) -> int:
        """Persist commodity candles to DB."""
        return save_candles_to_db(candles)

