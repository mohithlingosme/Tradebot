"""
Rob Booker Ziv Ghost Pivot Points.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass
class RobBookerZivGhostPivots:
    """Highlight pivots that remain untested for `ghost_lookback` sessions."""

    session_length: int = 78
    ghost_lookback: int = 5

    def calculate(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> Optional[Dict[str, List[float]]]:
        values = self.calculate_series(high, low, close)
        return values[-1] if values else None

    def calculate_series(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> List[Optional[Dict[str, List[float]]]]:
        if not (len(high) == len(low) == len(close)):
            return []
        outstanding: List[Dict[str, float]] = []
        output: List[Optional[Dict[str, List[float]]]] = []
        for idx in range(len(close)):
            session_idx = idx // self.session_length
            session_start = session_idx * self.session_length
            prev_start = session_start - self.session_length
            if prev_start < 0:
                output.append(None)
                continue
            prev_high = max(high[prev_start : prev_start + self.session_length])
            prev_low = min(low[prev_start : prev_start + self.session_length])
            prev_close = close[prev_start + self.session_length - 1]
            pivot = (prev_high + prev_low + prev_close) / 3.0
            session_slice = slice(session_start, session_start + self.session_length)
            touched = (
                min(low[session_slice]) <= pivot <= max(high[session_slice])
            )
            for entry in outstanding:
                entry["age"] += 1
            if not touched:
                outstanding.append({"pivot": pivot, "age": 0})
            ghost_levels = [
                entry["pivot"] for entry in outstanding if entry["age"] >= self.ghost_lookback
            ]
            output.append({"ghost_pivots": ghost_levels})
        return output
