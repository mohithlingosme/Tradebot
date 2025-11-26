from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import tenacity

from market_data_ingestion.adapters import ADAPTER_REGISTRY, BaseMarketDataAdapter, get_adapter
from market_data_ingestion.adapters.base import NormalizedTick
from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.metrics import (
    ACTIVE_CONNECTIONS,
    INGESTION_REQUESTS,
    metrics_collector,
)
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)


class RealtimeIngestionPipeline:
    """Consumes ticks from adapters, validates, stores, and handles DLQ."""

    def __init__(self, storage: DataStorage, adapter_name: str, adapter_config: Dict[str, Any], symbols: List[str]):
        self.storage = storage
        self.adapter_name = adapter_name
        self.adapter_config = adapter_config
        self.symbols = symbols
        self.adapter: Optional[BaseMarketDataAdapter] = None
        self._stop_event = asyncio.Event()
        self.last_message_at: Optional[datetime] = None
        self.state: str = "DISCONNECTED"

    async def start(self):
        self.adapter = get_adapter(self.adapter_name, self.adapter_config)
        await self.adapter.connect()
        await self.adapter.subscribe(self.symbols)
        self.state = "CONNECTED"
        ACTIVE_CONNECTIONS.labels(type=self.adapter_name).inc()
        logger.info(f"{self.adapter_name} connected and subscribed: {self.symbols}")
        try:
            async for tick in self.adapter.stream():
                if self._stop_event.is_set():
                    break
                await self._handle_tick(tick)
        except Exception as exc:
            self.state = "RETRYING"
            logger.error(f"Adapter {self.adapter_name} failed: {exc}")
            await self._reconnect_with_backoff()
        finally:
            ACTIVE_CONNECTIONS.labels(type=self.adapter_name).dec()
            self.state = "DISCONNECTED"

    async def stop(self):
        self._stop_event.set()
        if self.adapter:
            await self.adapter.close()

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _reconnect_with_backoff(self):
        if not self.adapter:
            return
        logger.info(f"Reconnecting adapter {self.adapter_name}...")
        await self.adapter.connect()
        await self.adapter.subscribe(self.symbols)
        self.state = "CONNECTED"
        async for tick in self.adapter.stream():
            await self._handle_tick(tick)

    async def _handle_tick(self, tick: NormalizedTick):
        if not self._validate_tick(tick):
            await self.storage.insert_dlq(
                provider=self.adapter_name,
                symbol=tick.symbol,
                error="validation_failed",
                payload=tick.to_dict(),
            )
            return

        payload = tick.to_dict()
        try:
            await self.storage.insert_tick(payload)
            INGESTION_REQUESTS.labels(provider=self.adapter_name, symbol=tick.symbol, status="success").inc()
            metrics_collector.update_last_successful_ingestion(self.adapter_name)
            self.last_message_at = tick.ts_utc
        except Exception as exc:
            logger.error(f"Failed to store tick {tick.symbol}: {exc}")
            INGESTION_REQUESTS.labels(provider=self.adapter_name, symbol=tick.symbol, status="error").inc()
            await self.storage.insert_dlq(
                provider=self.adapter_name,
                symbol=tick.symbol,
                error=str(exc),
                payload=payload,
            )

    def _validate_tick(self, tick: NormalizedTick) -> bool:
        if not tick.symbol or tick.price <= 0 or tick.volume < 0:
            return False
        if not isinstance(tick.ts_utc, datetime):
            return False
        return True
