"""
Elder Force Index implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .utils import ema_series, ensure_length


@dataclass
class ElderForceIndex:
    """Force index using price change multiplied by volume smoothed via EMA."""

    period: int = 13

    def calculate(
        self,
        close: Sequence[float],
        volume: Sequence[float],
    ) -> Optional[float]:
        values = self.calculate_series(close, volume)
        return values[-1]

    def calculate_series(
        self,
        close: Sequence[float],
        volume: Sequence[float],
    ) -> List[Optional[float]]:
        if len(close) != len(volume):
            return []
        if len(close) < 2:
            return [None] * len(close)
        raw = [0.0]
        for i in range(1, len(close)):
            raw.append((close[i] - close[i - 1]) * volume[i])
        ema_vals = ema_series(raw, self.period)
        return [float(val) for val in ema_vals]
