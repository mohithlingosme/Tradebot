"""Higher-level helpers to retrieve recent structured log entries."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import settings
from ..schemas.system import LogEntry

SEVERITY_ORDER: Dict[str, int] = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

SENSITIVE_KEYS = {"password", "secret", "token", "api_key", "apikey", "credentials"}


class LogAccessError(Exception):
    """Raised when the structured log store cannot be read."""


def _mask_sensitive_data(value: Any, key: Optional[str] = None) -> Any:
    """Recursively mask sensitive payloads."""
    if isinstance(value, dict):
        return {
            k: _mask_sensitive_data(v, k)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_mask_sensitive_data(item) for item in value]
    if key and any(s in key.lower() for s in SENSITIVE_KEYS):
        return "***REDACTED***"
    return value


def _extract_segments(message: str) -> tuple[str, Dict[str, Any], Optional[float], Optional[str]]:
    """Split message into the base text plus structured segments."""
    segments = [segment.strip() for segment in message.split(" | ")]
    base_message = segments[0] if segments else message.strip()
    data_payload: Dict[str, Any] = {}
    duration_ms: Optional[float] = None
    trace_id: Optional[str] = None

    for segment in segments[1:]:
        if segment.startswith("Data: "):
            payload = segment[6:].strip()
            try:
                data_payload = _mask_sensitive_data(json.loads(payload))
            except json.JSONDecodeError:
                data_payload = {"raw": payload}
        elif segment.startswith("Trace: "):
            trace_id = segment[7:].strip()
        elif segment.startswith("Duration: "):
            amount = segment[10:].strip()
            if amount.endswith("ms"):
                amount = amount[:-2]
            try:
                duration_ms = float(amount)
            except (ValueError, TypeError):
                duration_ms = None
        else:
            key, sep, value = segment.partition(": ")
            if sep:
                clean_key = key.strip()
                cleaned_value = value.strip()
                data_payload[clean_key] = _mask_sensitive_data(cleaned_value, clean_key)

    return base_message, data_payload, duration_ms, trace_id


class LoggingManager:
    """Manage controlled access to recent structured log entries."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    async def fetch_recent_logs(
        self,
        level: str,
        limit: int,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> List[LogEntry]:
        return await asyncio.to_thread(
            self._read_logs,
            level,
            limit,
            since,
            until,
        )

    def _read_logs(
        self,
        level: str,
        limit: int,
        since: datetime | None,
        until: datetime | None,
    ) -> List[LogEntry]:
        log_path = Path(settings.log_file)
        if not log_path.exists():
            message = f"Log file {log_path} does not exist"
            self._logger.error(message)
            raise LogAccessError(message)

        max_lines = min(max(limit * 5, 500), settings.log_scan_limit)
        try:
            with log_path.open("r", encoding="utf-8") as handle:
                raw_lines = deque(handle, maxlen=max_lines)
        except OSError as exc:
            message = f"Unable to read log file {log_path}: {exc}"
            self._logger.error(message)
            raise LogAccessError(message) from exc

        results: List[LogEntry] = []
        severity_threshold = SEVERITY_ORDER.get(level.upper(), SEVERITY_ORDER["INFO"])

        for raw_line in reversed(raw_lines):
            parsed = self._parse_line(raw_line)
            if not parsed:
                continue
            if not self._passes_filters(parsed, severity_threshold, since, until):
                continue
            results.append(parsed)
            if len(results) >= limit:
                break

        return results

    def _parse_line(self, raw_line: str) -> Optional[LogEntry]:
        text = raw_line.strip()
        if not text:
            return None

        parts = text.split(" - ", 3)
        if len(parts) < 4:
            return None

        timestamp_str, logger_name, level, remainder = parts

        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
        except ValueError:
            return None

        component = None
        message_text = remainder
        if remainder.startswith("["):
            closing = remainder.find("]")
            if closing != -1:
                component = remainder[1:closing]
                message_text = remainder[closing + 1 :].strip()

        base_message, data_payload, duration_ms, trace_id = _extract_segments(message_text)
        extra_fields: Dict[str, Any] = {}
        if component:
            extra_fields["component"] = component
        if data_payload:
            extra_fields["data"] = data_payload
        if duration_ms is not None:
            extra_fields["duration_ms"] = duration_ms

        return LogEntry(
            timestamp=timestamp,
            level=level.upper(),
            message=base_message,
            logger=logger_name.strip() or None,
            trace_id=trace_id,
            extra=extra_fields or None,
        )

    def _passes_filters(
        self,
        entry: LogEntry,
        severity_threshold: int,
        since: datetime | None,
        until: datetime | None,
    ) -> bool:
        entry_level = SEVERITY_ORDER.get(entry.level.upper(), 0)
        if entry_level < severity_threshold:
            return False
        if since and entry.timestamp < since:
            return False
        if until and entry.timestamp > until:
            return False
        return True
