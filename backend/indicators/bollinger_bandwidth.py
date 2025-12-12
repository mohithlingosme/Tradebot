"""
Bollinger Bandwidth Indicator

Measures the width of the Bollinger Bands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np


@dataclass
class BollingerBandwidth:
    """Bollinger Bandwidth indicator."""

    period: int = 20
    std_dev: float = 2.0

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        """Return the bandwidth value for the latest period."""
        if len(close) < self.period:
            return None

        # Calculate SMA
        sma = np.mean(close[-self.period:])

        # Calculate standard deviation
        std = np.std(close[-self.period:])

        # Upper and lower bands
        upper = sma + (self.std_dev * std)
        lower = sma - (self.std_dev * std)

        # Bandwidth
        if sma == 0:
            return 0.0

        bandwidth = (upper - lower) / sma

        return float(bandwidth)

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        """Return bandwidth series."""
        bandwidth_values = []
        for i in range(len(close)):
            if i < self.period - 1:
                bandwidth_values.append(None)
            else:
                sma = np.mean(close[i - self.period + 1 : i + 1])
                std = np.std(close[i - self.period + 1 : i + 1])
                upper = sma + (self.std_dev * std)
                lower = sma - (self.std_dev * std)
                if sma == 0:
                    bandwidth_values.append(0.0)
                else:
                    bandwidth = (upper - lower) / sma
                    bandwidth_values.append(float(bandwidth))
        return bandwidth_values
