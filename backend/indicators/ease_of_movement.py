"""
Ease of Movement indicator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class EaseOfMovement:
    """Quantifies how easily price moves as a function of range and volume."""

    def calculate(
        self,
        high: Sequence[float],
        low: Sequence[float],
        volume: Sequence[float],
    ) -> Optional[float]:
        values = self.calculate_series(high, low, volume)
        return values[-1] if values else None

    def calculate_series(
        self,
        high: Sequence[float],
        low: Sequence[float],
        volume: Sequence[float],
    ) -> List[Optional[float]]:
        if not (len(high) == len(low) == len(volume)):
            return []
        emv: List[Optional[float]] = [None]
        for i in range(1, len(high)):
            distance_moved = ((high[i] + low[i]) / 2) - ((high[i - 1] + low[i - 1]) / 2)
            box_ratio = (volume[i] / 100000000) / (high[i] - low[i]) if (high[i] - low[i]) != 0 else np.nan
            value = distance_moved / box_ratio if box_ratio not in (0, np.nan) else 0.0
            emv.append(value)
        return emv
