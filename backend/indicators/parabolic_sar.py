"""
Parabolic SAR Indicator

Trend-following indicator that provides entry and exit points.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class ParabolicSAR:
    """Parabolic SAR indicator."""

    acceleration: float = 0.02
    max_acceleration: float = 0.2

    def calculate(self, high: Sequence[float], low: Sequence[float]) -> Optional[float]:
        """Return the Parabolic SAR value for the latest period."""
        if len(high) < 3 or len(low) < 3:
            return None

        # Simplified calculation - in practice, this requires tracking trend direction
        # For now, return a basic approximation
        return float(low[-1] + self.acceleration * (high[-1] - low[-1]))

    def calculate_series(self, high: Sequence[float], low: Sequence[float]) -> List[Optional[float]]:
        """Return Parabolic SAR series."""
        if len(high) != len(low):
            return []
        sar_values = []
        trend_up = True
        acceleration = self.acceleration
        sar = low[0] if trend_up else high[0]

        for i in range(len(high)):
            sar_values.append(float(sar))

            if trend_up:
                if high[i] > high[i-1] if i > 0 else True:
                    acceleration = min(acceleration + self.acceleration, self.max_acceleration)
                sar = sar + acceleration * (high[i] - sar)
                if low[i] < sar:
                    trend_up = False
                    sar = high[i]
                    acceleration = self.acceleration
            else:
                if low[i] < low[i-1] if i > 0 else True:
                    acceleration = min(acceleration + self.acceleration, self.max_acceleration)
                sar = sar - acceleration * (sar - low[i])
                if high[i] > sar:
                    trend_up = True
                    sar = low[i]
                    acceleration = self.acceleration

        return sar_values
