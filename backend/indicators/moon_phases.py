"""
Approximate moon phase calculator to support lunar-based trading filters.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Sequence, Union


SYNODIC_PERIOD = 29.53058867  # days
REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)


def _to_datetime(value: Union[float, datetime]) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromtimestamp(value, tz=timezone.utc)


@dataclass
class MoonPhases:
    """Return descriptive moon phases for supplied timestamps."""

    def calculate(self, timestamps: Sequence[Union[float, datetime]]) -> Optional[str]:
        series = self.calculate_series(timestamps)
        return series[-1] if series else None

    def calculate_series(self, timestamps: Sequence[Union[float, datetime]]) -> List[Optional[str]]:
        phases: List[Optional[str]] = []
        for stamp in timestamps:
            dt = _to_datetime(stamp)
            days_since = (dt - REFERENCE_NEW_MOON).total_seconds() / 86400.0
            if days_since < 0:
                phases.append(None)
                continue
            cycle_position = days_since % SYNODIC_PERIOD
            if cycle_position < 1.84566:
                phases.append("new")
            elif cycle_position < 5.53699:
                phases.append("waxing_crescent")
            elif cycle_position < 9.22831:
                phases.append("first_quarter")
            elif cycle_position < 12.91963:
                phases.append("waxing_gibbous")
            elif cycle_position < 16.61096:
                phases.append("full")
            elif cycle_position < 20.30228:
                phases.append("waning_gibbous")
            elif cycle_position < 23.99361:
                phases.append("last_quarter")
            else:
                phases.append("waning_crescent")
        return phases
