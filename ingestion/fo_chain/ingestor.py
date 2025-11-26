from __future__ import annotations

"""Ingest futures and options chains into normalized candle form."""

from datetime import datetime
from typing import Any, List, Mapping, Sequence

try:
    import yfinance as yf  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yf = None

from common.market_data import Candle, normalize_to_candles
from ingestion.base import BaseIngestor, save_candles_to_db


class FOChainIngestor(BaseIngestor):
    """
    Convert options/futures chain snapshots into Candle rows.

    For option chains we collapse the best available price into an OHLC candle
    at the time of ingestion to make downstream processing consistent.
    """

    def __init__(self, source: str = "yfinance", timeframe: str = "1d") -> None:
        self.source = source
        self.timeframe = timeframe
        self._last_symbol: str | None = None

    def fetch_raw(self, symbol: str, expiry_dates: Sequence[str] | None = None, **kwargs: Any) -> Any:
        """Fetch option chain data using the configured provider."""
        self._last_symbol = symbol
        if "raw" in kwargs:
            return kwargs["raw"]
        if self.source.lower() != "yfinance":
            raise ValueError(f"Unsupported FO chain source: {self.source}")
        if yf is None:
            raise RuntimeError("yfinance is required for FO chain ingestion")

        ticker = yf.Ticker(symbol)
        expiries = expiry_dates or getattr(ticker, "options", []) or []
        selected_expiries = expiries if expiry_dates else expiries[:1]
        now = datetime.utcnow()
        records: List[Mapping[str, Any]] = []

        for expiry in selected_expiries:
            chain = ticker.option_chain(expiry)
            for side_name in ("calls", "puts"):
                df = getattr(chain, side_name, None)
                if df is None or df.empty:
                    continue
                for _, row in df.iterrows():
                    last_price = float(row.get("lastPrice") or 0.0)
                    bid = float(row.get("bid") or 0.0)
                    ask = float(row.get("ask") or 0.0)
                    strike = float(row.get("strike") or 0.0)
                    base_price = (bid + ask) / 2 if (bid and ask) else bid or ask or strike
                    price = last_price or base_price or strike
                    records.append(
                        {
                            "symbol": symbol,
                            "timestamp": now,
                            "open": price,
                            "high": max(price, float(row.get("highPrice") or price)),
                            "low": min(price, float(row.get("lowPrice") or price)),
                            "close": price,
                            "volume": float(row.get("volume") or 0.0),
                        }
                    )

        return {"symbol": symbol, "records": records}

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
        """Normalize chain snapshots to candles."""
        records: Sequence[Mapping[str, Any]] = []
        if isinstance(raw, Mapping) and "records" in raw:
            records = raw.get("records") or []
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            records = raw

        symbol = self._resolve_symbol(raw, records)
        if not symbol:
            raise ValueError("Symbol required to normalize chain data")

        return normalize_to_candles(records, symbol=symbol, timeframe=self.timeframe, source=self.source)

    def save(self, candles: List[Candle]) -> int:
        """Persist normalized chain candles."""
        return save_candles_to_db(candles)
