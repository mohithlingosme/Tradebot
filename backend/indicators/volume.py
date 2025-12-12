"""
Simple volume utility indicator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class VolumeIndicator:
    """Return cumulative or latest volume depending on configuration."""

    aggregate: bool = False
    period: int = 24

    def calculate(self, volume: Sequence[float]) -> Optional[float]:
        if not volume:
            return None
        if not self.aggregate:
            return float(volume[-1])
        if len(volume) < self.period:
            return None
        window = volume[-self.period :]
        return float(sum(window))

    def calculate_series(self, volume: Sequence[float]) -> List[Optional[float]]:
        values: List[Optional[float]] = []
        for i in range(len(volume)):
            values.append(self.calculate(volume[: i + 1]))
        return values
