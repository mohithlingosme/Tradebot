"""
Chaikin Money Flow helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class ChaikinMoneyFlow:
    """Expose :meth:`VolumeIndicators.chaikin_money_flow`."""

    period: int = 20

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
        return VolumeIndicators.chaikin_money_flow(
            high=high, low=low, close=close, volume=volume, period=self.period
        )
