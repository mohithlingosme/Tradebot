"""
Rob Booker missed pivot tracker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass
class RobBookerMissedPivotPoints:
    """Track pivot levels derived from the prior session that price failed to tag."""

    session_length: int = 78

    def calculate(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> Optional[Dict[str, List[Dict[str, float]]]]:
        values = self.calculate_series(high, low, close)
        return values[-1] if values else None

    def calculate_series(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
    ) -> List[Optional[Dict[str, List[Dict[str, float]]]]]:
        if not (len(high) == len(low) == len(close)):
            return []
        missed: List[Dict[str, float]] = []
        output: List[Optional[Dict[str, List[Dict[str, float]]]]] = []
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
            session_high = max(high[session_start : session_start + self.session_length])
            session_low = min(low[session_start : session_start + self.session_length])
            touched = session_low <= pivot <= session_high
            age = session_idx
            for entry in missed:
                entry["age"] += 1
            if not touched:
                missed.append({"pivot": pivot, "age": 0})
            output.append({"missed": list(missed)})
        return output
