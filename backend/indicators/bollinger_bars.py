"""
Bollinger Bars classification helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .bollinger_bands import BollingerBands


@dataclass
class BollingerBars:
    """Tag each bar depending on where it closes relative to the bands."""

    period: int = 20
    std_dev_multiplier: float = 2.0

    def calculate(self, close: Sequence[float]) -> Optional[str]:
        series = self.calculate_series(close)
        return series[-1]

    def calculate_series(self, close: Sequence[float]) -> List[Optional[str]]:
        bands = BollingerBands(period=self.period, std_dev_multiplier=self.std_dev_multiplier)
        band_series = bands.calculate_series(list(close))
        labels: List[Optional[str]] = []
        for idx, data in enumerate(band_series):
            if data is None:
                labels.append(None)
                continue
            price = close[idx]
            if price >= data["upper_band"]:
                labels.append("touch_upper")
            elif price <= data["lower_band"]:
                labels.append("touch_lower")
            elif price >= data["middle_band"]:
                labels.append("upper_half")
            else:
                labels.append("lower_half")
        return labels
