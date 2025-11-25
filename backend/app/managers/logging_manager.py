"""Higher-level helpers to retrieve log data."""

from datetime import datetime, timedelta
from typing import List

from ..schemas.system import LogEntry


class LoggingManager:
    """Manage controlled access to recent log lines."""

    async def fetch_recent_logs(self, level: str, limit: int) -> List[LogEntry]:
        now = datetime.utcnow()
        base_level = level.upper() if level else "INFO"
        logs = []

        for index in range(limit):
            entry = LogEntry(
                timestamp=now - timedelta(seconds=index * 15),
                level=base_level,
                message=f"Mock log entry #{index + 1} for level {base_level}",
                source="finbot.backend.logger",
            )
            logs.append(entry)

        return logs
