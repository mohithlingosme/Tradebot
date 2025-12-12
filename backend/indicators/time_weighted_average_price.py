"""
Time Weighted Average Price helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class TimeWeightedAveragePrice:
    """Wrap :meth:`VolumeIndicators.time_weighted_average_price`."""

    def calculate(self, prices: Sequence[float], timestamps: Sequence[float]) -> float:
        return VolumeIndicators.time_weighted_average_price(prices=prices, timestamps=timestamps)
