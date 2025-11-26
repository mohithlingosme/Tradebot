from __future__ import annotations

import asyncio
import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp
import tenacity

from market_data_ingestion.adapters import get_adapter
from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.logging_config import get_logger
from market_data_ingestion.src.metrics import DATA_POINTS_INGESTED

logger = get_logger(__name__)


REQUIRED_FIELDS = {"symbol", "ts_utc", "open", "high", "low", "close", "volume", "provider"}


def _parse_csv_rows(content: str) -> List[Dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(content))
    return [row for row in reader]


def _validate_row(row: Dict[str, Any]) -> bool:
    if not REQUIRED_FIELDS.issubset(row.keys()):
        return False
    try:
        if float(row["open"]) < 0 or float(row["high"]) < 0 or float(row["low"]) < 0 or float(row["close"]) < 0:
            return False
    except Exception:
        return False
    return True


async def ingest_csv(storage: DataStorage, csv_content: str, provider: str) -> Dict[str, int]:
    rows = _parse_csv_rows(csv_content)
    processed = skipped = 0
    for row in rows:
        if not _validate_row(row):
            await storage.insert_dlq(provider, row.get("symbol"), "validation_failed", row)
            skipped += 1
            continue
        await storage.insert_candle(row)
        processed += 1
    DATA_POINTS_INGESTED.labels(provider=provider, data_type="csv").inc(processed)
    return {"processed": processed, "skipped": skipped}


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def fetch_csv(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


async def backfill_api(
    storage: DataStorage,
    adapter_name: str,
    adapter_config: Dict[str, Any],
    symbols: List[str],
    start: str,
    end: str,
    interval: str = "1m",
) -> Dict[str, int]:
    adapter = get_adapter(adapter_name, adapter_config)
    await adapter.connect()
    await adapter.subscribe(symbols)
    processed = skipped = 0
    for symbol in symbols:
        try:
            # Prefer provider-specific fetchers if available
            if hasattr(adapter, "fetch_historical_data"):
                data = await adapter.fetch_historical_data(symbol, start, end, interval)  # type: ignore[attr-defined]
            elif hasattr(adapter, "fetch_klines"):
                data = await adapter.fetch_klines(symbol, interval=interval)  # type: ignore[attr-defined]
            else:
                raise NotImplementedError("Adapter does not support backfill")
            for candle in data:
                if not _validate_row(candle):
                    await storage.insert_dlq(adapter.provider, symbol, "validation_failed", candle)
                    skipped += 1
                    continue
                await storage.insert_candle(candle)
                processed += 1
            DATA_POINTS_INGESTED.labels(provider=adapter.provider, data_type="api").inc(len(data))
        except Exception as exc:
            logger.error(f"Backfill failed for {symbol} via {adapter.provider}: {exc}")
            await storage.insert_dlq(adapter.provider, symbol, str(exc), {"start": start, "end": end})
    await adapter.close()
    return {"processed": processed, "skipped": skipped}
