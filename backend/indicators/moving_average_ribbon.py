"""
Moving Average Ribbon helper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .moving_average import EMA


@dataclass
class MovingAverageRibbon:
    """Compute a family of EMAs to visualize ribbon steepness."""

    periods: List[int] = field(default_factory=lambda: [8, 13, 21, 34, 55])

    def calculate(self, close: Sequence[float]) -> Optional[Dict[int, float]]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[int, float]]]:
        ribbons: List[Optional[Dict[int, float]]] = []
        ema_instances = {period: EMA(period) for period in self.periods}
        for idx in range(len(close)):
            snapshot: Dict[int, float] = {}
            for period, indicator in ema_instances.items():
                value = indicator.calculate(list(close[: idx + 1]))
                if value is not None:
                    snapshot[period] = value
            ribbons.append(snapshot if snapshot else None)
        return ribbons
