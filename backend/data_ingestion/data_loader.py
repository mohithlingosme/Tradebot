"""
Data Loader Module

Responsibilities:
- Read data from storage layer
- Supply data to strategy engine
- Handle data resampling and caching

Interfaces:
- load_historical_data(symbol, start_date, end_date, interval)
- load_real_time_data(symbol)
- resample_data(data, target_interval)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

try:
    from ..core.cache import CacheManager, cache_manager
except ImportError:  # pragma: no cover - optional dependency in some environments
    CacheManager = None
    cache_manager = None

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Module for loading market data from storage and supplying to trading engine.
    Handles caching, resampling, and data preprocessing.
    """

    def __init__(self, storage_config: Dict, cache_config: Optional[Dict] = None):
        """
        Initialize data loader with storage and cache configuration.

        Args:
            storage_config: Configuration for data storage (e.g., database connection)
            cache_config: Optional cache configuration (e.g., Redis settings)
        """
        self.storage_config = storage_config
        self.cache_config = cache_config or {}
        self.logger = logging.getLogger(f"{__name__}.DataLoader")
        self.db_url = self._resolve_db_url()
        self.engine: Engine = create_engine(self.db_url, future=True)
        self.cache_ttl = self.cache_config.get("ttl", 300)
        self.cache = self._init_cache()

    def load_historical_data(self, symbol: str, start_date: datetime,
                           end_date: datetime, interval: str = '1m') -> Optional[Dict]:
        """
        Load historical data for backtesting or analysis.

        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            interval: Time interval

        Returns:
            Dictionary containing historical data or None if not found
        """
        cache_key = self._build_cache_key(
            "historical", symbol, interval, start_date.isoformat(), end_date.isoformat()
        )
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        query = text(
            """
            SELECT symbol, ts_utc, open, high, low, close, volume, provider
            FROM candles
            WHERE symbol = :symbol
              AND ts_utc BETWEEN :start AND :end
            ORDER BY ts_utc ASC
            """
        )
        params = {
            "symbol": symbol.upper(),
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }
        rows = self._execute_query(query, params)

        if not rows:
            self.logger.warning("No historical data found for %s", symbol)
            return None

        payload = {
            "symbol": symbol.upper(),
            "interval": interval,
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "count": len(rows),
            "data": [self._normalize_row(row) for row in rows],
        }
        self._cache_set(cache_key, payload)
        return payload

    def load_real_time_data(self, symbol: str) -> Optional[Dict]:
        """
        Load latest real-time data for live trading.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary containing real-time data or None if not available
        """
        cache_key = self._build_cache_key("realtime", symbol)
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        query = text(
            """
            SELECT symbol, ts_utc, open, high, low, close, volume, provider
            FROM candles
            WHERE symbol = :symbol
            ORDER BY ts_utc DESC
            LIMIT 1
            """
        )
        params = {"symbol": symbol.upper()}
        rows = self._execute_query(query, params)
        if not rows:
            self.logger.warning("No realtime data found for %s", symbol)
            return None

        latest = self._normalize_row(rows[0])
        self._cache_set(cache_key, latest, ttl=self.cache_config.get("realtime_ttl", 30))
        return latest

    def resample_data(self, data: Dict, target_interval: str) -> Dict:
        """
        Resample data to target time interval.

        Args:
            data: Original data dictionary
            target_interval: Target interval ('1m', '5m', '1h', etc.)

        Returns:
            Resampled data dictionary
        """
        if not data or not data.get("data"):
            return data

        freq = self._interval_to_freq(target_interval)
        if not freq:
            self.logger.warning("Unsupported resample interval %s", target_interval)
            return data

        df = pd.DataFrame(data["data"])
        if df.empty:
            return data

        df["ts_utc"] = pd.to_datetime(df["ts_utc"])
        df = df.set_index("ts_utc").sort_index()

        ohlc = df[["open", "high", "low", "close"]].resample(freq).agg(
            {"open": "first", "high": "max", "low": "min", "close": "last"}
        )
        volume = df["volume"].resample(freq).sum()
        provider_series = None
        if "provider" in df.columns:
            provider_series = df["provider"].resample(freq).last()

        resampled_records: List[Dict[str, Any]] = []
        for ts, row in ohlc.dropna().iterrows():
            resampled_records.append(
                {
                    "symbol": data["symbol"],
                    "ts_utc": ts.isoformat(),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(volume.get(ts, 0.0)),
                    "provider": self._resolve_provider(provider_series, ts, data),
                }
            )

        return {
            **data,
            "interval": target_interval,
            "count": len(resampled_records),
            "data": resampled_records,
        }

    def preload_data(self, symbols: List[str], days: int = 30) -> bool:
        """
        Preload data for multiple symbols to improve performance.

        Args:
            symbols: List of symbols to preload
            days: Number of days of historical data to preload

        Returns:
            True if preload successful, False otherwise
        """
        self.logger.info("Preloading data for %s symbols (%s days)", len(symbols), days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        success = True
        for symbol in symbols:
            try:
                result = self.load_historical_data(symbol, start_date, end_date)
                success = success and result is not None
            except Exception as exc:  # pragma: no cover - defensive programming
                self.logger.error("Failed to preload %s: %s", symbol, exc)
                success = False
        return success

    # Internal helpers --------------------------------------------------------

    def _resolve_db_url(self) -> str:
        if "db_url" in self.storage_config:
            return self.storage_config["db_url"]
        if "connection_string" in self.storage_config:
            return self.storage_config["connection_string"]
        db_path = self.storage_config.get("path", "market_data.db")
        if db_path.startswith("sqlite:///"):
            return db_path
        return f"sqlite:///{db_path}"

    def _init_cache(self):
        if not self.cache_config.get("enabled", True):
            return None
        if CacheManager is None:
            return None

        redis_url = self.cache_config.get("redis_url") or self.cache_config.get("url")
        if not redis_url:
            return cache_manager if cache_manager else None

        try:
            return CacheManager(redis_url=redis_url, default_ttl=self.cache_ttl)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Cache disabled (failed to init redis): %s", exc)
            return None

    def _cache_get(self, key: str) -> Optional[Dict]:
        if not self.cache:
            return None
        return self.cache.get(key)

    def _cache_set(self, key: str, value: Dict, ttl: Optional[int] = None):
        if not self.cache:
            return
        self.cache.set(key, value, ttl=ttl or self.cache_ttl)

    def _build_cache_key(self, *parts: str) -> str:
        return ":".join(part.strip().lower() for part in parts if part)

    def _execute_query(self, query, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            with self.engine.connect() as connection:
                result = connection.execute(query, params)
                return [dict(row) for row in result.mappings()]
        except SQLAlchemyError as exc:
            self.logger.error("Database query failed: %s", exc)
            return []

    def _normalize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = row.get("ts_utc")
        if isinstance(timestamp, datetime):
            ts_value = timestamp.isoformat()
        else:
            ts_value = str(timestamp)

        return {
            "symbol": row.get("symbol"),
            "ts_utc": ts_value,
            "open": float(row.get("open", 0.0)),
            "high": float(row.get("high", 0.0)),
            "low": float(row.get("low", 0.0)),
            "close": float(row.get("close", 0.0)),
            "volume": float(row.get("volume", 0.0)),
            "provider": row.get("provider", "unknown"),
        }

    def _interval_to_freq(self, interval: str) -> Optional[str]:
        mapping = {
            "1m": "1T",
            "3m": "3T",
            "5m": "5T",
            "15m": "15T",
            "30m": "30T",
            "1h": "1H",
            "4h": "4H",
            "1d": "1D",
        }
        return mapping.get(interval.lower())

    def _resolve_provider(self, provider_series, timestamp: pd.Timestamp, original: Dict) -> str:
        if provider_series is not None:
            try:
                value = provider_series.loc[timestamp]
                if isinstance(value, str):
                    return value
            except KeyError:
                pass
        return (original.get("data") or [{}])[-1].get("provider", "unknown")
