"""
Rob Booker intraday pivot points (classic floor pivots with daily roll overs).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


@dataclass
class RobBookerIntradayPivotPoints:
    """Derive intraday pivot levels from the previous session."""

    session_length: int = 78  # assume 5 minute bars during regular hours

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[Dict[str, float]]:
        values = self.calculate_series(high, low, close)
        return values[-1] if values else None

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        if not (len(high) == len(low) == len(close)):
            return []
        pivots: List[Optional[Dict[str, float]]] = []
        for idx in range(len(close)):
            session_idx = idx // self.session_length
            session_start = session_idx * self.session_length
            prev_start = session_start - self.session_length
            if prev_start < 0:
                pivots.append(None)
                continue
            prev_slice = slice(prev_start, prev_start + self.session_length)
            prev_high = max(high[prev_slice])
            prev_low = min(low[prev_slice])
            prev_close = close[prev_start + self.session_length - 1]
            pivot = (prev_high + prev_low + prev_close) / 3.0
            range_val = prev_high - prev_low
            pivots.append(
                {
                    "pivot": pivot,
                    "r1": pivot + range_val,
                    "s1": pivot - range_val,
                    "r2": pivot + 2 * range_val,
                    "s2": pivot - 2 * range_val,
                }
            )
        return pivots
