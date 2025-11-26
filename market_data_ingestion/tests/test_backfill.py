import os
import sys

import pytest

repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, repo_root)

from market_data_ingestion.core.backfill import ingest_csv
from market_data_ingestion.core.storage import DataStorage


@pytest.mark.asyncio
async def test_ingest_csv_to_candles(tmp_path):
    db_url = f"sqlite:///{tmp_path}/bf.db"
    storage = DataStorage(db_url)
    await storage.connect()
    await storage.create_tables()

    csv_content = """symbol,ts_utc,open,high,low,close,volume,provider
AAPL,2024-01-01T00:00:00Z,1,2,1,2,100,yfinance"""
    res = await ingest_csv(storage, csv_content, provider="yfinance")

    assert res["processed"] == 1
    cursor = await storage.conn.execute("SELECT COUNT(*) FROM candles")
    row = await cursor.fetchone()
    await cursor.close()
    assert row[0] == 1
