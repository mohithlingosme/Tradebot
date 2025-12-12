"""
Volume Weighted Moving Average helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class VolumeWeightedMovingAverage:
    """Convenience wrapper around :meth:`VolumeIndicators.volume_weighted_moving_average`."""

    period: int = 20

    def calculate(self, close: Sequence[float], volume: Sequence[float]) -> Optional[float]:
        return VolumeIndicators.volume_weighted_moving_average(
            close_prices=close, volume=volume, period=self.period
        )
