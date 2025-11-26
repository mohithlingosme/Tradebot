from __future__ import annotations

"""
Macro & economic indicator scraper (Phase 3.3).
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Sequence

import httpx
import yfinance as yf

from .config import DataCollectorSettings, get_settings
from .db import PostgresClient
from .models import MacroIndicator

logger = logging.getLogger(__name__)


@dataclass
class MacroMetricConfig:
    metric_name: str
    provider: str  # "yfinance" | "worldbank" | custom
    identifier: str
    country_code: Optional[str] = None
    lookback_days: int = 365
    source: str = "macro"


DEFAULT_MACRO_METRICS: Sequence[MacroMetricConfig] = (
    MacroMetricConfig("india_vix", "yfinance", "^INDIAVIX", lookback_days=30, source="yfinance"),
    MacroMetricConfig("usd_inr", "yfinance", "INR=X", lookback_days=30, source="yfinance"),
    MacroMetricConfig("brent_crude", "yfinance", "BZ=F", lookback_days=60, source="yfinance"),
    MacroMetricConfig("wti_crude", "yfinance", "CL=F", lookback_days=60, source="yfinance"),
    MacroMetricConfig("gdp_india", "worldbank", "NY.GDP.MKTP.CD", country_code="IND", lookback_days=365 * 5, source="worldbank"),
    MacroMetricConfig("cpi_india", "worldbank", "FP.CPI.TOTL.ZG", country_code="IND", lookback_days=365 * 3, source="worldbank"),
    MacroMetricConfig("repo_rate_india", "worldbank", "FR.INR.RINR", country_code="IND", lookback_days=365 * 3, source="worldbank"),
)


class MacroScraper:
    """
    Fetches macro indicators from multiple providers and stores them in PostgreSQL.
    """

    def __init__(
        self,
        settings: Optional[DataCollectorSettings] = None,
        db: Optional[PostgresClient] = None,
        metrics: Sequence[MacroMetricConfig] = DEFAULT_MACRO_METRICS,
    ):
        self.settings = settings or get_settings()
        self.db = db or PostgresClient(self.settings.database_url)
        self.metrics = list(metrics)

    async def __aenter__(self) -> "MacroScraper":
        await self.db.connect()
        await self.db.ensure_phase3_schema()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.db.close()

    async def _fetch_yfinance_metric(self, config: MacroMetricConfig) -> Optional[MacroIndicator]:
        def _worker() -> Optional[MacroIndicator]:
            ticker = yf.Ticker(config.identifier)
            history = ticker.history(period=f"{config.lookback_days}d", interval="1d")
            if history.empty:
                return None
            latest = history.tail(1)
            ts = latest.index[0]
            value = float(latest["Close"].iloc[0])
            return MacroIndicator(
                metric_name=config.metric_name,
                as_of_date=ts.date(),
                value=value,
                source=config.source,
            )

        return await asyncio.to_thread(_worker)

    async def _fetch_worldbank_metric(self, config: MacroMetricConfig) -> Optional[MacroIndicator]:
        if not config.country_code:
            logger.warning("WorldBank metric %s missing country_code", config.metric_name)
            return None

        url = (
            f"https://api.worldbank.org/v2/country/{config.country_code}"
            f"/indicator/{config.identifier}?format=json&per_page=60"
        )
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            payload = resp.json()
            if not isinstance(payload, list) or len(payload) < 2:
                return None
            entries = payload[1]
            for entry in entries:
                value = entry.get("value")
                if value is None:
                    continue
                try:
                    as_of_year = int(entry.get("date"))
                except Exception:
                    continue
                as_of_date = date(as_of_year, 12, 31)
                return MacroIndicator(
                    metric_name=config.metric_name,
                    as_of_date=as_of_date,
                    value=float(value),
                    source=config.source,
                )
        return None

    async def fetch_metric(self, config: MacroMetricConfig) -> Optional[MacroIndicator]:
        if config.provider == "yfinance":
            return await self._fetch_yfinance_metric(config)
        if config.provider == "worldbank":
            return await self._fetch_worldbank_metric(config)

        logger.warning("Unsupported macro provider %s for %s", config.provider, config.metric_name)
        return None

    async def fetch_latest(self) -> List[MacroIndicator]:
        tasks = [self.fetch_metric(config) for config in self.metrics]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        indicators: List[MacroIndicator] = []
        for config, result in zip(self.metrics, results):
            if isinstance(result, Exception):
                logger.warning("Failed to fetch %s: %s", config.metric_name, result)
                continue
            if result:
                indicators.append(result)
        return indicators

    async def persist(self, indicators: Sequence[MacroIndicator]) -> None:
        if not indicators:
            return

        query = """
        INSERT INTO macro_indicators (
            metric_name, as_of_date, value, source, created_at
        ) VALUES (
            $1, $2, $3, $4, NOW()
        )
        ON CONFLICT (metric_name, as_of_date, source)
        DO UPDATE SET value = EXCLUDED.value
        """
        params = [
            (item.metric_name, item.as_of_date, item.value, item.source) for item in indicators
        ]
        await self.db.executemany(query, params)
        logger.info("Persisted %s macro indicators", len(indicators))

    async def run(self) -> List[MacroIndicator]:
        indicators = await self.fetch_latest()
        await self.persist(indicators)
        return indicators


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async with MacroScraper() as scraper:
        indicators = await scraper.run()
        for indicator in indicators:
            logger.info("Captured macro metric %s = %s on %s", indicator.metric_name, indicator.value, indicator.as_of_date)


if __name__ == "__main__":
    asyncio.run(main())
