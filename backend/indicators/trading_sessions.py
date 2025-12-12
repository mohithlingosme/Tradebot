"""
Trading session classifier.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Sequence, Union


def _normalize_timestamp(value: Union[float, datetime]) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromtimestamp(value, tz=timezone.utc)


@dataclass
class TradingSessions:
    """Tag each timestamp with the dominant FX/Equity session."""

    def calculate(self, timestamps: Sequence[Union[float, datetime]]) -> Optional[str]:
        series = self.calculate_series(timestamps)
        return series[-1] if series else None

    def calculate_series(self, timestamps: Sequence[Union[float, datetime]]) -> List[Optional[str]]:
        sessions: List[Optional[str]] = []
        for ts in timestamps:
            dt = _normalize_timestamp(ts)
            hour = dt.hour
            if 23 <= hour or hour < 7:
                sessions.append("asia")
            elif 7 <= hour < 13:
                sessions.append("europe")
            elif 13 <= hour < 20:
                sessions.append("us")
            else:
                sessions.append("after_hours")
        return sessions
