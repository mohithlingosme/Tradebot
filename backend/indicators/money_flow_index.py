"""
Money Flow Index helper that reuses the vectorised implementation in
``VolumeIndicators``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class MoneyFlowIndex:
    """MFI wrapper built on :class:`backend.indicators.volume_indicators.VolumeIndicators`."""

    period: int = 14

    def calculate(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
        volume: Sequence[float],
    ) -> Optional[float]:
        series = self.calculate_series(high, low, close, volume)
        return series[-1] if series else None

    def calculate_series(
        self,
        high: Sequence[float],
        low: Sequence[float],
        close: Sequence[float],
        volume: Sequence[float],
    ) -> List[Optional[float]]:
        return VolumeIndicators.money_flow_index(
            high=high, low=low, close=close, volume=volume, period=self.period
        )
