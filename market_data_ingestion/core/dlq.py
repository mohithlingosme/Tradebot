from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)


async def reprocess_dlq(storage: DataStorage, limit: int = 100) -> int:
    """Simple DLQ reprocessor that replays stored payloads into tick storage."""
    if storage.db_type == "sqlite":
        cursor = await storage.conn.execute("SELECT id, provider, symbol, payload FROM dlq_events ORDER BY id LIMIT ?", (limit,))
        rows = await cursor.fetchall()
        await cursor.close()
    else:
        rows = await storage.conn.fetch("SELECT id, provider, symbol, payload FROM dlq_events ORDER BY id LIMIT $1", limit)

    processed = 0
    for row in rows:
        payload = row[3] if storage.db_type == "sqlite" else row["payload"]
        try:
            await storage.insert_tick(payload)
            processed += 1
            # Delete processed DLQ entry
            if storage.db_type == "sqlite":
                await storage.conn.execute("DELETE FROM dlq_events WHERE id = ?", (row[0],))
                await storage.conn.commit()
            else:
                await storage.conn.execute("DELETE FROM dlq_events WHERE id = $1", row["id"])
        except Exception as exc:
            logger.error(f"Failed to reprocess DLQ id {row[0]}: {exc}")
    return processed
