"""
On-Balance Volume helper backed by :mod:`backend.indicators.volume_indicators`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .volume_indicators import VolumeIndicators


@dataclass
class OnBalanceVolume:
    """Convenience wrapper returning OBV values."""

    def calculate(self, close: Sequence[float], volume: Sequence[float]) -> Optional[float]:
        series = self.calculate_series(close, volume)
        return series[-1] if series else None

    def calculate_series(self, close: Sequence[float], volume: Sequence[float]) -> List[float]:
        return VolumeIndicators.on_balance_volume(close_prices=close, volume=volume)
