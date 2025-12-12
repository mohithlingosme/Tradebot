"""
24 Hour Volume Indicator

Calculates the total traded volume over a 24-hour period or specified lookback window.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class TwentyFourHourVolume:
    """24 Hour Volume indicator."""

    lookback: int = 24

    def calculate(self, volume: Sequence[float]) -> Optional[float]:
        """Return the total volume over the lookback period."""
        if len(volume) < self.lookback:
            return None
        return float(np.sum(volume[-self.lookback:]))

    def calculate_series(self, volume: Sequence[float]) -> List[Optional[float]]:
        """Return rolling total volumes."""
        volumes = []
        for i in range(len(volume)):
            if i < self.lookback - 1:
                volumes.append(None)
            else:
                vol_sum = np.sum(volume[i - self.lookback + 1 : i + 1])
                volumes.append(float(vol_sum))
        return volumes
