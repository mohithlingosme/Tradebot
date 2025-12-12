"""
Advance/Decline ratio based on bar closes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class AdvanceDeclineRationBars:
    """Compute the ratio of advancing closes to declining closes."""

    lookback: int = 20

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        closes = list(float(v) for v in close)
        output: List[Optional[float]] = []
        if len(closes) < 2:
            return [None] * len(closes)
        changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        output.append(None)
        for i in range(1, len(closes)):
            start = max(0, i - self.lookback + 1)
            look_changes = changes[start:i]
            advances = sum(1 for c in look_changes if c > 0)
            declines = sum(1 for c in look_changes if c < 0)
            if declines == 0:
                ratio = float(advances) if advances else None
            else:
                ratio = advances / declines
            output.append(ratio)
        return output
