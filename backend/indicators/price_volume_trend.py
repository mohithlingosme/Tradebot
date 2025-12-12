"""
Price Volume Trend wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class PriceVolumeTrend:
    """Expose PVT via a dedicated class."""

    def calculate(self, close: Sequence[float], volume: Sequence[float]) -> float:
        return self.calculate_series(close, volume)[-1]

    def calculate_series(self, close: Sequence[float], volume: Sequence[float]) -> List[float]:
        return VolumeIndicators.price_volume_trend(close_prices=close, volume=volume)
