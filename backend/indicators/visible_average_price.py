"""
Visible Average Price helper (average of the currently selected range).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass
class VisibleAveragePrice:
    """Compute the mean close for the visible portion of a chart."""

    start_index: int = 0

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        if self.start_index >= len(close):
            return None
        window = close[self.start_index :]
        if not window:
            return None
        return float(sum(window) / len(window))
