"""
Cumulative Volume Delta helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class CumulativeVolumeDelta:
    """Expose the static helper via an instance-friendly API."""

    def calculate(self, buy_volume: Sequence[float], sell_volume: Sequence[float]) -> float:
        return self.calculate_series(buy_volume, sell_volume)[-1]

    def calculate_series(self, buy_volume: Sequence[float], sell_volume: Sequence[float]) -> List[float]:
        return VolumeIndicators.cumulative_volume_delta(buy_volume=buy_volume, sell_volume=sell_volume)
