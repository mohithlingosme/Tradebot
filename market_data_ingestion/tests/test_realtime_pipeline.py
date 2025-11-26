import os
import sys
from datetime import datetime, timezone

import pytest

repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, repo_root)

from market_data_ingestion.adapters.base import BaseMarketDataAdapter, NormalizedTick
from market_data_ingestion.core.realtime import RealtimeIngestionPipeline
from market_data_ingestion.core.storage import DataStorage


class DummyAdapter(BaseMarketDataAdapter):
    provider = "dummy"

    def __init__(self, config):
        super().__init__(config)
        self._ticks = config.get("ticks", [])

    async def connect(self):
        await self._mark_connected(True)

    async def close(self):
        await self._mark_connected(False)

    async def subscribe(self, symbols):
        self.symbols = symbols

    async def stream(self):
        for tick in self._ticks:
            yield tick


@pytest.mark.asyncio
async def test_pipeline_happy_path(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/test.db"
    storage = DataStorage(db_url)
    await storage.connect()
    await storage.create_tables()

    tick = NormalizedTick(
        symbol="AAPL",
        ts_utc=datetime.now(timezone.utc),
        price=150.0,
        volume=10,
        provider="dummy",
        raw={"foo": "bar"},
    )

    # Patch registry to use dummy adapter
    from market_data_ingestion import adapters as registry

    registry.ADAPTER_REGISTRY["dummy"] = DummyAdapter

    pipeline = RealtimeIngestionPipeline(storage, "dummy", {"ticks": [tick]}, ["AAPL"])
    await pipeline._handle_tick(tick)

    # Verify tick inserted
    cursor = await storage.conn.execute("SELECT COUNT(*) FROM ticks")
    row = await cursor.fetchone()
    await cursor.close()
    assert row[0] == 1


@pytest.mark.asyncio
async def test_pipeline_validation_to_dlq(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path}/test.db"
    storage = DataStorage(db_url)
    await storage.connect()
    await storage.create_tables()

    bad_tick = NormalizedTick(
        symbol="AAPL",
        ts_utc=datetime.now(timezone.utc),
        price=-1.0,
        volume=1,
        provider="dummy",
        raw={},
    )

    from market_data_ingestion import adapters as registry

    registry.ADAPTER_REGISTRY["dummy"] = DummyAdapter

    pipeline = RealtimeIngestionPipeline(storage, "dummy", {"ticks": [bad_tick]}, ["AAPL"])
    await pipeline._handle_tick(bad_tick)

    cursor = await storage.conn.execute("SELECT COUNT(*) FROM dlq_events")
    row = await cursor.fetchone()
    await cursor.close()
    assert row[0] == 1
