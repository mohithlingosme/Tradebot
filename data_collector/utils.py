from __future__ import annotations

"""
Utilities shared across scrapers.
"""

import hashlib
import logging
from datetime import date, datetime
from itertools import islice
from pathlib import Path
from typing import Generator, Iterable, List, Sequence
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def ensure_directory(path: str | Path) -> Path:
    """Create directory if it does not exist."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def to_market_date(dt: datetime, tz: str = "Asia/Kolkata") -> date:
    """
    Convert a datetime to a market date in the given timezone.
    """
    zone = ZoneInfo(tz)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(zone).date()


def stable_hash(value: str) -> str:
    """Stable short hash for deduplication."""
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def chunked(iterable: Sequence, size: int) -> Generator[List, None, None]:
    """
    Yield successive n-sized chunks from a sequence or iterable.
    """
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk

