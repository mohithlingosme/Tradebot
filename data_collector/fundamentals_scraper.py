from __future__ import annotations

"""
Fundamentals scraper (Phase 3.4).
"""

import argparse
import asyncio
import logging
from datetime import date, timedelta
from typing import List, Optional, Sequence

import yfinance as yf

from .config import DataCollectorSettings, get_settings
from .db import PostgresClient
from .models import FundamentalRecord

logger = logging.getLogger(__name__)


class FundamentalsScraper:
    """Fetches and stores quarterly fundamentals for tracked symbols."""

    def __init__(self, settings: Optional[DataCollectorSettings] = None, db: Optional[PostgresClient] = None):
        self.settings = settings or get_settings()
        self.db = db or PostgresClient(self.settings.database_url)

    async def __aenter__(self) -> "FundamentalsScraper":
        await self.db.connect()
        await self.db.ensure_phase3_schema()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.db.close()

    def _fetch_symbol_yfinance(self, symbol: str) -> List[FundamentalRecord]:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        fundamentals_df = ticker.quarterly_financials
        records: List[FundamentalRecord] = []

        if fundamentals_df is None or fundamentals_df.empty:
            logger.warning("No fundamentals returned for %s", symbol)
            return records

        # Transpose so that rows are quarters
        df = fundamentals_df.T
        for period_end, row in df.iterrows():
            period_end_date: date = getattr(period_end, "date", lambda: period_end)()
            period_start_date = period_end_date - timedelta(days=90)

            records.append(
                FundamentalRecord(
                    symbol=symbol,
                    period_start=period_start_date,
                    period_end=period_end_date,
                    period_type="quarterly",
                    pe=info.get("trailingPE"),
                    eps=info.get("trailingEps"),
                    roe=info.get("returnOnEquity"),
                    revenue=float(row.get("Total Revenue", row.get("TotalRevenue", 0)) or 0),
                    profit=float(row.get("Net Income", row.get("NetIncome", 0)) or 0),
                    market_cap=info.get("marketCap"),
                    source="yfinance",
                    currency=info.get("currency", "INR"),
                )
            )
        return records

    async def fetch_symbol(self, symbol: str) -> List[FundamentalRecord]:
        return await asyncio.to_thread(self._fetch_symbol_yfinance, symbol)

    async def persist(self, records: Sequence[FundamentalRecord]) -> None:
        if not records:
            return

        query = """
        INSERT INTO fundamentals (
            symbol, period_start, period_end, period_type, pe, eps, roe,
            revenue, profit, market_cap, source, currency, updated_at, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW()
        )
        ON CONFLICT (symbol, period_start, period_end, source)
        DO UPDATE SET
            pe = EXCLUDED.pe,
            eps = EXCLUDED.eps,
            roe = EXCLUDED.roe,
            revenue = EXCLUDED.revenue,
            profit = EXCLUDED.profit,
            market_cap = EXCLUDED.market_cap,
            currency = EXCLUDED.currency,
            updated_at = NOW()
        """
        params = [
            (
                r.symbol,
                r.period_start,
                r.period_end,
                r.period_type,
                r.pe,
                r.eps,
                r.roe,
                r.revenue,
                r.profit,
                r.market_cap,
                r.source,
                r.currency,
            )
            for r in records
        ]
        await self.db.executemany(query, params)
        logger.info("Persisted %s fundamental rows", len(records))

    async def refresh_symbol(self, symbol: str) -> List[FundamentalRecord]:
        records = await self.fetch_symbol(symbol)
        await self.persist(records)
        return records

    async def refresh_all(self, symbols: Sequence[str]) -> None:
        for symbol in symbols:
            try:
                await self.refresh_symbol(symbol)
            except Exception as exc:
                logger.error("Failed to refresh fundamentals for %s: %s", symbol, exc)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh fundamentals for symbols")
    parser.add_argument("--symbols", nargs="+", help="Symbols to refresh. Defaults to configured universe.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    symbols = args.symbols or settings.default_symbols

    async with FundamentalsScraper(settings=settings) as scraper:
        await scraper.refresh_all(symbols)


if __name__ == "__main__":
    asyncio.run(main())

