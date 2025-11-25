"""Minimal async-safe caching helper."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Tuple


class SimpleCache:
    """Thread-safe enough for asynchronous workloads with short TTLs."""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[Any, datetime]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if not entry:
            return None
        value, expires = entry
        if expires < datetime.utcnow():
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (
            value,
            datetime.utcnow() + timedelta(seconds=ttl_seconds),
        )

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)
