"""
Auto-anchored VWAP helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class VWAPAutoAnchored:
    """Compute anchored VWAP values from an anchor index."""

    anchor_index: int = 0

    def calculate(
        self,
        close: Sequence[float],
        volume: Sequence[float],
    ) -> float:
        values = self.calculate_series(close, volume)
        return values[-1]

    def calculate_series(
        self,
        close: Sequence[float],
        volume: Sequence[float],
    ) -> List[float]:
        return VolumeIndicators.anchored_vwap(close_prices=close, volume=volume, anchor_index=self.anchor_index)
