from __future__ import annotations

"""CSV logging helpers for raw ticks."""

import csv
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, IO, Optional, Tuple

logger = logging.getLogger(__name__)


class CSVLogger:
    """
    Persist ticks to data/raw/{symbol}_{date}.csv.

    Usage:
        with CSVLogger() as logger:
            logger.log_tick("BTCUSD", datetime.utcnow(), 42000.0, 0.5)
    """

    def __init__(self, base_dir: str | Path = "data/raw") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._handles: Dict[Path, Tuple[IO[str], csv.writer]] = {}
        self._lock = Lock()

    def log_tick(self, symbol: str, ts: datetime, price: float, volume: float | None) -> Path:
        """
        Append a tick row to the daily CSV file.
        """
        volume_value = volume if volume is not None else 0.0
        filename = f"{symbol}_{ts.strftime('%Y-%m-%d')}.csv"
        path = self.base_dir / filename
        iso_ts = ts.isoformat()

        with self._lock:
            file_handle, writer = self._ensure_writer(path)
            writer.writerow([iso_ts, symbol, price, volume_value])
            file_handle.flush()
        logger.debug("Logged tick %s %s -> %s", symbol, iso_ts, path)
        return path

    def _ensure_writer(self, path: Path) -> Tuple[IO[str], csv.writer]:
        if path in self._handles:
            return self._handles[path]
        handle = path.open("a", newline="", encoding="utf-8")
        writer = csv.writer(handle)
        if path.stat().st_size == 0:
            writer.writerow(["timestamp", "symbol", "price", "volume"])
            handle.flush()
        self._handles[path] = (handle, writer)
        return self._handles[path]

    def close(self) -> None:
        with self._lock:
            for handle, _ in self._handles.values():
                handle.close()
            self._handles.clear()

    def __enter__(self) -> "CSVLogger":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> Optional[bool]:
        self.close()
        return None
