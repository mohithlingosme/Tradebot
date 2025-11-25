"""
Data Fetcher Module

Responsibilities:
- Fetch historical and real-time market data from multiple sources
- Normalize/clean the data (OHLC checks, missing values)
- Push data to storage layer

Interfaces:
- fetch_historical_data(symbol, start_date, end_date, interval)
- fetch_real_time_data(symbol)
- validate_and_clean_data(data)
"""

import logging
import math
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - optional dependency at runtime
    yf = None

try:
    from alpha_vantage.timeseries import TimeSeries
except ImportError:  # pragma: no cover - optional dependency at runtime
    TimeSeries = None

import pandas as pd

logger = logging.getLogger(__name__)

class DataFetcher:
    """
    Service for fetching market data from various sources.
    Supports multiple data providers with fallback mechanisms.
    """

    def __init__(self, config: Dict):
        """
        Initialize data fetcher with configuration.

        Args:
            config: Configuration dictionary containing API keys, endpoints, etc.
        """
        self.config = config
        self.sources = config.get('data_sources', [])
        self.logger = logging.getLogger(f"{__name__}.DataFetcher")

    def fetch_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = '1m'
    ) -> Optional[Dict]:
        """
        Fetch historical OHLC data for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'NSE:RELIANCE')
            start_date: Start date for data
            end_date: End date for data
            interval: Time interval ('1m', '5m', '1h', etc.)

        Returns:
            Dictionary containing OHLC data or None if failed
        """
        self.logger.info(
            "Fetching historical data for %s between %s and %s (%s interval)",
            symbol,
            start_date.isoformat(),
            end_date.isoformat(),
            interval,
        )

        sources = self.sources or [{"name": "yfinance", "type": "yfinance", "enabled": True}]
        for source in sources:
            if not source.get("enabled", True):
                continue

            source_name = source.get("name", source.get("type", "unknown"))
            try:
                records = self._fetch_historical_from_source(
                    source, symbol, start_date, end_date, interval
                )
                if not records:
                    continue

                cleaned_records = [self.validate_and_clean_data(record) for record in records]
                metadata = {
                    "symbol": symbol.upper(),
                    "source": source_name,
                    "interval": interval,
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "records": cleaned_records,
                }
                self.logger.info(
                    "Fetched %s candles for %s using %s", len(cleaned_records), symbol, source_name
                )
                return metadata
            except Exception as exc:  # pragma: no cover - network calls mocked in tests
                self.logger.warning(
                    "Source %s failed to fetch %s: %s", source_name, symbol, exc
                )

        self.logger.error("All data sources failed to return data for %s", symbol)
        return None

    def fetch_real_time_data(self, symbol: str) -> Optional[Dict]:
        """
        Fetch real-time market data for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Dictionary containing current market data or None if failed
        """
        self.logger.info("Fetching real-time quote for %s", symbol)

        sources = self.sources or [{"name": "yfinance", "type": "yfinance", "enabled": True}]
        for source in sources:
            if not source.get("enabled", True):
                continue

            source_type = source.get("type", "yfinance").lower()
            try:
                if source_type == "yfinance":
                    realtime_data = self._fetch_realtime_from_yfinance(symbol)
                elif source_type == "alphavantage":
                    realtime_data = self._fetch_realtime_from_alphavantage(symbol, source)
                else:
                    self.logger.debug("Skipping unsupported realtime source %s", source_type)
                    continue

                if realtime_data:
                    return self.validate_and_clean_data(realtime_data)
            except Exception as exc:  # pragma: no cover - external dependency
                self.logger.warning("Realtime source %s failed: %s", source_type, exc)

        self.logger.error("No real-time data available for %s", symbol)
        return None

    def validate_and_clean_data(self, data: Dict) -> Dict:
        """
        Validate and clean raw market data.

        Args:
            data: Raw data dictionary

        Returns:
            Cleaned and validated data dictionary
        """
        cleaned = data.copy()
        required_fields = ("open", "high", "low", "close", "volume")

        # Replace missing numeric values
        fallback_price = cleaned.get("close") or cleaned.get("open") or 0.0
        for field in required_fields:
            value = cleaned.get(field)
            if value is None or (isinstance(value, float) and math.isnan(value)):
                cleaned[field] = float(fallback_price if field != "volume" else 0.0)

        cleaned["volume"] = max(float(cleaned["volume"]), 0.0)

        # Normalize OHLC relationships
        ohlc_values = [
            float(cleaned["open"]),
            float(cleaned["high"]),
            float(cleaned["low"]),
            float(cleaned["close"]),
        ]
        high = max(ohlc_values)
        low = min(ohlc_values)
        cleaned["high"] = high
        cleaned["low"] = low

        # Clamp obvious outliers using median-based rule
        median_price = statistics.median(ohlc_values)
        if median_price > 0:
            max_deviation = 5.0  # Allow up to 500% deviation before clamping
            for field in ("open", "high", "low", "close"):
                price = float(cleaned[field])
                if abs(price - median_price) / median_price > max_deviation:
                    self.logger.warning(
                        "Detected outlier for %s (%.2f). Clamping to median %.2f",
                        field,
                        price,
                        median_price,
                    )
                    cleaned[field] = median_price

        timestamp = cleaned.get("ts_utc")
        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            cleaned["ts_utc"] = timestamp.isoformat()
        else:
            cleaned["ts_utc"] = str(timestamp)

        cleaned["symbol"] = (cleaned.get("symbol") or "UNKNOWN").upper()
        cleaned.setdefault("provider", "unknown")
        cleaned.setdefault("type", "candle")

        return cleaned

    def get_data_sources(self) -> List[str]:
        """
        Get list of available data sources.

        Returns:
            List of data source names
        """
        return [source['name'] for source in self.sources]

    # Internal helper methods -------------------------------------------------

    def _fetch_historical_from_source(
        self,
        source: Dict,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> List[Dict]:
        source_type = source.get("type", "yfinance").lower()
        if source_type == "yfinance":
            return self._fetch_historical_from_yfinance(symbol, start_date, end_date, interval)
        if source_type == "alphavantage":
            return self._fetch_historical_from_alphavantage(symbol, start_date, end_date, interval, source)

        raise ValueError(f"Unsupported data source type: {source_type}")

    def _fetch_historical_from_yfinance(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> List[Dict]:
        if yf is None:
            raise RuntimeError("yfinance is not installed")

        df = yf.download(
            symbol,
            start=start_date,
            end=end_date + timedelta(days=1),
            interval=interval,
            progress=False,
        )
        if df.empty:
            return []

        df = df.sort_index()
        candles: List[Dict] = []
        for ts, row in df.iterrows():
            candles.append(
                {
                    "symbol": symbol,
                    "ts_utc": ts.to_pydatetime().replace(tzinfo=timezone.utc),
                    "type": "candle",
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row.get("Volume", 0.0)),
                    "provider": "yfinance",
                    "meta": {"interval": interval},
                }
            )
        return candles

    def _fetch_historical_from_alphavantage(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        source: Dict,
    ) -> List[Dict]:
        if TimeSeries is None:
            raise RuntimeError("alpha_vantage is not installed")

        api_key = source.get("api_key") or self.config.get("alphavantage_api_key")
        if not api_key:
            raise ValueError("Alpha Vantage API key not configured")

        ts = TimeSeries(key=api_key, output_format="pandas")
        interval_lower = interval.lower()
        if interval_lower.endswith("m"):
            df, _ = ts.get_intraday(
                symbol=symbol,
                interval=interval_lower,
                outputsize=source.get("outputsize", "compact"),
            )
        else:
            df, _ = ts.get_daily_adjusted(
                symbol=symbol,
                outputsize=source.get("outputsize", "compact"),
            )

        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df = df.loc[(df.index >= start_date) & (df.index <= end_date)]

        column_map = {
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
            "5. volume": "volume",
        }

        candles: List[Dict] = []
        for ts_idx, row in df.iterrows():
            normalized = {target: float(row[source]) for source, target in column_map.items() if source in row}
            normalized.update(
                {
                    "symbol": symbol,
                    "ts_utc": ts_idx.to_pydatetime().replace(tzinfo=timezone.utc),
                    "type": "candle",
                    "provider": "alphavantage",
                    "meta": {"interval": interval},
                }
            )
            candles.append(normalized)
        return candles

    def _fetch_realtime_from_yfinance(self, symbol: str) -> Optional[Dict]:
        if yf is None:
            raise RuntimeError("yfinance is not installed")

        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d", interval="1m")
        if hist.empty:
            return None

        last_row = hist.iloc[-1]
        timestamp = last_row.name.to_pydatetime().replace(tzinfo=timezone.utc)
        return {
            "symbol": symbol,
            "ts_utc": timestamp,
            "type": "realtime",
            "open": float(last_row["Open"]),
            "high": float(last_row["High"]),
            "low": float(last_row["Low"]),
            "close": float(last_row["Close"]),
            "volume": float(last_row.get("Volume", 0.0)),
            "provider": "yfinance",
        }

    def _fetch_realtime_from_alphavantage(self, symbol: str, source: Dict) -> Optional[Dict]:
        if TimeSeries is None:
            raise RuntimeError("alpha_vantage is not installed")

        api_key = source.get("api_key") or self.config.get("alphavantage_api_key")
        if not api_key:
            raise ValueError("Alpha Vantage API key not configured")

        ts = TimeSeries(key=api_key, output_format="json")
        quote, _ = ts.get_quote_endpoint(symbol=symbol)
        if not quote:
            return None

        timestamp_str = quote.get("07. latest trading day", datetime.utcnow().isoformat())
        timestamp = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
        return {
            "symbol": symbol,
            "ts_utc": timestamp,
            "type": "realtime",
            "open": float(quote.get("02. open", 0.0)),
            "high": float(quote.get("03. high", 0.0)),
            "low": float(quote.get("04. low", 0.0)),
            "close": float(quote.get("05. price", 0.0)),
            "volume": float(quote.get("06. volume", 0.0)),
            "provider": "alphavantage",
        }
