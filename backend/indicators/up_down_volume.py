"""
Up/Down volume helper built on :class:`NetVolume`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class UpDownVolume:
    """Provide the same value as the net-volume calculation."""

    def calculate(self, up_volume: Sequence[float], down_volume: Sequence[float]) -> float:
        return self.calculate_series(up_volume, down_volume)[-1]

    def calculate_series(self, up_volume: Sequence[float], down_volume: Sequence[float]) -> List[float]:
        return VolumeIndicators.net_volume(up_volume=up_volume, down_volume=down_volume)
