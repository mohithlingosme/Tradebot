"""
Volume Delta helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class VolumeDelta:
    """Compute the change in volume from one bar to the next."""

    def calculate(self, volume: Sequence[float]) -> Optional[float]:
        if len(volume) < 2:
            return None
        return float(volume[-1] - volume[-2])

    def calculate_series(self, volume: Sequence[float]) -> List[Optional[float]]:
        deltas: List[Optional[float]] = [None]
        for i in range(1, len(volume)):
            deltas.append(float(volume[i] - volume[i - 1]))
        return deltas
