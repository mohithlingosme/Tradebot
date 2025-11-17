import csv
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import yaml

from market_data_ingestion.adapters.yfinance import YFinanceAdapter
from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class BackfillConfig:
    symbols: List[str]
    period: str
    interval: str
    csv_file: Optional[str] = None


class BackfillRunner:
    """Reusable helper that performs historical data backfill operations."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).resolve().parents[2] / "config" / "config.example.yaml"
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as handle:
            self.config = yaml.safe_load(handle)
        self.storage = DataStorage(self.config["database"]["db_path"])
        self.adapter = YFinanceAdapter(self.config["providers"]["yfinance"])

    async def __aenter__(self):
        await self.storage.connect()
        await self.storage.create_tables()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.storage.disconnect()

    async def run(self, backfill_config: BackfillConfig) -> int:
        """Perform the backfill and return number of symbols processed."""
        symbols = self._resolve_symbols(backfill_config)
        if not symbols:
            raise ValueError("No symbols provided for backfill run")

        period_days = int(backfill_config.period.rstrip("d"))
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

        processed = 0
        for idx, symbol in enumerate(symbols, 1):
            logger.info(
                "Backfilling %s (%s/%s) from %s to %s interval=%s",
                symbol,
                idx,
                len(symbols),
                start_date,
                end_date,
                backfill_config.interval,
            )
            try:
                candles = await self.adapter.fetch_historical_data(
                    symbol, start_date, end_date, backfill_config.interval
                )
                for candle in candles:
                    await self.storage.insert_candle(candle)
                processed += 1
                logger.info("Stored %s candles for %s", len(candles), symbol)
            except Exception as exc:  # pragma: no cover - network-heavy block
                logger.error("Backfill failed for %s: %s", symbol, exc)
        return processed

    def _resolve_symbols(self, config: BackfillConfig) -> List[str]:
        if config.csv_file:
            return self._load_symbols_from_csv(config.csv_file)
        return config.symbols

    def _load_symbols_from_csv(self, csv_file: str) -> List[str]:
        path = Path(csv_file)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")
        symbols: List[str] = []
        with open(path, "r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                symbol = row.get("symbol")
                if symbol:
                    symbols.append(symbol.strip())
        logger.info("Loaded %s symbols from %s", len(symbols), csv_file)
        return symbols


async def run_backfill_from_config(
    symbols: Optional[List[str]] = None,
    period: Optional[str] = None,
    interval: Optional[str] = None,
    csv_file: Optional[str] = None,
) -> int:
    """Utility for callers that just want to trigger a backfill with overrides."""
    async with BackfillRunner() as runner:
        config = runner.config.get("pipelines", {}).get("backfill", {})
        resolved_config = BackfillConfig(
            symbols=symbols or config.get("symbols", []),
            period=period or config.get("period", "1d"),
            interval=interval or config.get("interval", "1m"),
            csv_file=csv_file,
        )
        return await runner.run(resolved_config)

