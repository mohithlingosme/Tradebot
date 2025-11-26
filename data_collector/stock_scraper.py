from __future__ import annotations

"""
Stock & index data scraper (Phase 3.1).
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pandas as pd
import yfinance as yf

from .config import DataCollectorSettings, get_settings
from .db import PostgresClient
from .models import Anomaly, AnomalyType, PriceBar

logger = logging.getLogger(__name__)


class StockScraper:
    """
    Fetches OHLCV data from yfinance (or NSEPy if available) and persists to PostgreSQL.
    """

    def __init__(self, settings: Optional[DataCollectorSettings] = None, db: Optional[PostgresClient] = None):
        self.settings = settings or get_settings()
        self.db = db or PostgresClient(self.settings.database_url)

    async def __aenter__(self) -> "StockScraper":
        await self.db.connect()
        await self.db.ensure_phase3_schema()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.db.close()

    def load_symbols(self) -> List[str]:
        """
        Resolve the list of symbols to track. Priority:
        1. symbols_file (newline delimited)
        2. settings.default_symbols
        """
        if self.settings.symbols_file:
            path = Path(self.settings.symbols_file)
            if path.exists():
                symbols = [line.strip() for line in path.read_text().splitlines() if line.strip()]
                if symbols:
                    return symbols

        return list(self.settings.default_symbols)

    async def fetch_ohlcv_range(
        self,
        symbols: Sequence[str],
        start: date,
        end: Optional[date] = None,
        interval: str = "1d",
    ) -> List[PriceBar]:
        """
        Fetch OHLCV for a list of symbols between start and end dates.
        """
        end = end or date.today()
        tasks = [
            asyncio.to_thread(self._download_symbol_history, symbol, start, end, interval)
            for symbol in symbols
        ]
        results: List[List[PriceBar]] = await asyncio.gather(*tasks)
        bars: List[PriceBar] = []
        for symbol_bars in results:
            bars.extend(symbol_bars)
        return bars

    def _download_symbol_history(
        self, symbol: str, start: date, end: date, interval: str = "1d"
    ) -> List[PriceBar]:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end + timedelta(days=1), interval=interval, actions=False)
        if df.empty:
            logger.warning("No data returned for %s between %s and %s", symbol, start, end)
            return []

        df = df.reset_index()
        bars: List[PriceBar] = []
        for _, row in df.iterrows():
            ts: datetime = row["Date"]
            bars.append(
                PriceBar(
                    symbol=symbol,
                    trade_date=ts.date(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                    provider="yfinance",
                    is_index=False,
                )
            )
        return bars

    async def fetch_sector_indices(self, start: date, end: Optional[date] = None) -> List[PriceBar]:
        end = end or date.today()
        tasks = [
            asyncio.to_thread(self._download_symbol_history, ticker, start, end, "1d")
            for ticker in self.settings.sector_indices.values()
        ]
        results: List[List[PriceBar]] = await asyncio.gather(*tasks)
        bars: List[PriceBar] = []
        for index_name, index_bars in zip(self.settings.sector_indices.keys(), results):
            for bar in index_bars:
                bars.append(bar.copy(update={"symbol": index_name, "is_index": True}))
        return bars

    @staticmethod
    def detect_anomalies(bars: List[PriceBar], volume_window: int = 20, price_window: int = 5) -> List[Anomaly]:
        """
        Detect simple anomalies: volume spikes, price gaps, and large returns.
        """
        if not bars:
            return []

        df = pd.DataFrame([bar.model_dump() for bar in bars]).sort_values(["symbol", "trade_date"])
        df["volume_ma"] = (
            df.groupby("symbol")["volume"].rolling(volume_window, min_periods=5).mean().reset_index(level=0, drop=True)
        )
        df["prev_close"] = df.groupby("symbol")["close"].shift(1)
        df["gap_pct"] = (df["open"] - df["prev_close"]) / df["prev_close"]
        df["ret_pct"] = df.groupby("symbol")["close"].pct_change()

        anomalies: List[Anomaly] = []
        for _, row in df.iterrows():
            trade_date: date = row["trade_date"]
            symbol = row["symbol"]

            if row.get("volume_ma") and row["volume_ma"] > 0:
                if row["volume"] > row["volume_ma"] * 2.5:
                    anomalies.append(
                        Anomaly(
                            symbol=symbol,
                            trade_date=trade_date,
                            anomaly_type=AnomalyType.VOLUME_SPIKE,
                            metric_value=float(row["volume"]),
                            reference_value=float(row["volume_ma"]),
                            magnitude=float(row["volume"] / row["volume_ma"]),
                        )
                    )

            if row.get("gap_pct") and abs(row["gap_pct"]) >= 0.02:
                anomalies.append(
                    Anomaly(
                        symbol=symbol,
                        trade_date=trade_date,
                        anomaly_type=AnomalyType.PRICE_GAP,
                        metric_value=float(row["gap_pct"]),
                        reference_value=float(row["prev_close"]) if row.get("prev_close") else None,
                        magnitude=abs(float(row["gap_pct"])),
                    )
                )

            if row.get("ret_pct") and abs(row["ret_pct"]) >= 0.04:
                anomalies.append(
                    Anomaly(
                        symbol=symbol,
                        trade_date=trade_date,
                        anomaly_type=AnomalyType.PRICE_MOVE,
                        metric_value=float(row["ret_pct"]),
                        reference_value=float(row["prev_close"]) if row.get("prev_close") else None,
                        magnitude=abs(float(row["ret_pct"])),
                    )
                )

        return anomalies

    async def persist_prices(self, bars: List[PriceBar]) -> None:
        if not bars:
            return

        query = """
        INSERT INTO daily_prices (
            symbol, trade_date, open_price, high_price, low_price, close_price,
            volume, provider, is_index, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW()
        )
        ON CONFLICT (symbol, trade_date, provider)
        DO UPDATE SET
            open_price = EXCLUDED.open_price,
            high_price = EXCLUDED.high_price,
            low_price = EXCLUDED.low_price,
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume,
            updated_at = NOW(),
            is_index = EXCLUDED.is_index
        """

        params = [
            (
                bar.symbol,
                bar.trade_date,
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.volume,
                bar.provider,
                bar.is_index,
            )
            for bar in bars
        ]
        await self.db.executemany(query, params)
        logger.info("Persisted %s price rows", len(bars))

    async def persist_anomalies(self, anomalies: List[Anomaly]) -> None:
        if not anomalies:
            return

        query = """
        INSERT INTO price_anomalies (
            symbol, trade_date, anomaly_type, metric_value, reference_value, magnitude, details, provider, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, NOW()
        )
        ON CONFLICT (symbol, trade_date, anomaly_type, provider)
        DO UPDATE SET
            metric_value = EXCLUDED.metric_value,
            reference_value = EXCLUDED.reference_value,
            magnitude = EXCLUDED.magnitude,
            details = EXCLUDED.details
        """
        params = [
            (
                anomaly.symbol,
                anomaly.trade_date,
                anomaly.anomaly_type.value,
                anomaly.metric_value,
                anomaly.reference_value,
                anomaly.magnitude,
                anomaly.details,
                anomaly.provider,
            )
            for anomaly in anomalies
        ]
        await self.db.executemany(query, params)
        logger.info("Persisted %s anomalies", len(anomalies))

    async def fetch_and_store_latest(self, days: int = 10) -> Tuple[int, int]:
        """
        Fetch the latest daily bars for tracked symbols plus sector indices and persist.
        Returns tuple of (price_rows, anomaly_rows) counts.
        """
        symbols = self.load_symbols()
        start = date.today() - timedelta(days=days)
        bars = await self.fetch_ohlcv_range(symbols, start=start)
        index_bars = await self.fetch_sector_indices(start=start)
        all_bars = bars + index_bars

        await self.persist_prices(all_bars)

        anomalies = self.detect_anomalies(all_bars)
        await self.persist_anomalies(anomalies)
        return len(all_bars), len(anomalies)


async def main() -> None:
    """Convenience CLI entrypoint."""
    logging.basicConfig(level=logging.INFO)
    async with StockScraper() as scraper:
        price_count, anomaly_count = await scraper.fetch_and_store_latest(days=30)
        logger.info("Completed run: %s prices, %s anomalies", price_count, anomaly_count)


if __name__ == "__main__":
    asyncio.run(main())
