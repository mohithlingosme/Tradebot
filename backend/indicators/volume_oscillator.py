"""
Volume Oscillator helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class VolumeOscillator:
    """Wrap the static helper and expose standard fast/slow configuration."""

    fast_period: int = 5
    slow_period: int = 20

    def calculate(self, volume: Sequence[float]) -> Optional[float]:
        series = self.calculate_series(volume)
        return series[-1] if series else None

    def calculate_series(self, volume: Sequence[float]) -> List[Optional[float]]:
        return VolumeIndicators.volume_oscillator(volume=volume, fast_period=self.fast_period, slow_period=self.slow_period)
