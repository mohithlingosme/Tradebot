"""
Detrended Price Oscillator Indicator

Removes trend from price to identify cycles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class DetrendedPriceOscillator:
    """Detrended Price Oscillator indicator."""

    period: int = 20

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the DPO value for the latest period."""
        if len(close) < self.period * 2:
            return None

        # Calculate SMA
        sma = np.mean(close[-self.period * 2 + self.period // 2 : -self.period // 2 or None])

        # DPO
        dpo = close[-1] - sma

        return float(dpo)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return DPO series."""
        dpo_values = []
        for i in range(len(close)):
            if i < self.period * 2 - 1:
                dpo_values.append(None)
            else:
                start_idx = i - self.period * 2 + self.period // 2
                end_idx = i - self.period // 2
                sma = np.mean(close[start_idx : end_idx + 1])
                dpo = close[i] - sma
                dpo_values.append(float(dpo))
        return dpo_values
