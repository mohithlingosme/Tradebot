"""Scheduler unit tests covering auto refresh timing and retries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from market_data_ingestion.core import scheduler as scheduler_module
from market_data_ingestion.core.scheduler import AutoRefreshScheduler


def _write_config(path: Path) -> None:
    path.write_text(
        """
database:
  db_path: "sqlite:///tmp.db"
scheduler:
  auto_refresh:
    run_time: "00:00"
    timezone: "UTC"
    enabled: true
""",
        encoding="utf-8",
    )


def test_seconds_until_next_run_is_positive(tmp_path):
    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    scheduler = AutoRefreshScheduler(config_path=cfg)
    scheduler.settings.run_time = (datetime.now(timezone.utc) + timedelta(minutes=1)).strftime("%H:%M")
    seconds = scheduler._seconds_until_next_run()
    assert seconds > 0


@pytest.mark.asyncio
async def test_trigger_refresh_invokes_backfill(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    _write_config(cfg)
    scheduler = AutoRefreshScheduler(config_path=cfg)

    mocked = AsyncMock(return_value=3)
    monkeypatch.setattr(scheduler_module, "run_backfill_from_config", mocked)

    await scheduler.trigger_refresh()
    mocked.assert_awaited()
