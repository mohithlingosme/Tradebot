import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import yaml
from zoneinfo import ZoneInfo

from market_data_ingestion.core.tasks.backfill_runner import run_backfill_from_config
from market_data_ingestion.src.logging_config import get_logger


logger = get_logger(__name__)


@dataclass
class AutoRefreshSettings:
    """Configuration for the daily auto-refresh job."""

    run_time: str = "02:00"  # HH:MM
    timezone: str = "UTC"
    period: Optional[str] = None
    interval: Optional[str] = None
    symbols: Optional[List[str]] = None
    enabled: bool = True


class AutoRefreshScheduler:
    """Simple scheduler that triggers a market-data refresh once per day."""

    def __init__(
        self,
        settings: Optional[AutoRefreshSettings] = None,
        config_path: Optional[Path] = None,
    ):
        self.config_path = config_path or Path(__file__).resolve().parents[1] / "config" / "config.example.yaml"
        self._config = self._load_config()
        settings_from_file = self._load_settings_from_config()
        self.settings = settings or settings_from_file
        self._lock = asyncio.Lock()
        logger.info(
            "AutoRefreshScheduler initialized run_time=%s timezone=%s enabled=%s",
            self.settings.run_time,
            self.settings.timezone,
            self.settings.enabled,
        )

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    def _load_settings_from_config(self) -> AutoRefreshSettings:
        scheduler_cfg = self._config.get("scheduler", {}).get("auto_refresh", {})
        return AutoRefreshSettings(
            run_time=scheduler_cfg.get("run_time", "02:00"),
            timezone=scheduler_cfg.get("timezone", "UTC"),
            period=scheduler_cfg.get("period"),
            interval=scheduler_cfg.get("interval"),
            symbols=scheduler_cfg.get("symbols"),
            enabled=scheduler_cfg.get("enabled", True),
        )

    def _seconds_until_next_run(self) -> float:
        tz = ZoneInfo(self.settings.timezone)
        now = datetime.now(tz)
        hour, minute = (int(part) for part in self.settings.run_time.split(":"))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target = target + timedelta(days=1)
        delta = target - now
        return max(delta.total_seconds(), 1.0)

    async def run_forever(self):
        """Run the scheduler loop indefinitely."""
        if not self.settings.enabled:
            logger.warning("Auto refresh disabled via configuration")
            return

        while True:
            wait_seconds = self._seconds_until_next_run()
            logger.info("Next auto-refresh scheduled in %.2f seconds", wait_seconds)
            await asyncio.sleep(wait_seconds)
            await self.trigger_refresh()

    async def trigger_refresh(self):
        """Trigger the refresh job immediately."""
        async with self._lock:
            logger.info("Starting scheduled auto-refresh job")
            processed = await run_backfill_from_config(
                symbols=self.settings.symbols,
                period=self.settings.period,
                interval=self.settings.interval,
            )
            logger.info("Auto-refresh job completed processed=%s", processed)

