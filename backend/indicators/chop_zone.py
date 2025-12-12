"""
Chop Zone indicator built on the choppiness index.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .choppiness_index import ChoppinessIndex


@dataclass
class ChopZone:
    """Classify market regime based on the choppiness index."""

    period: int = 14
    choppy_threshold: float = 61.8
    trending_threshold: float = 38.2

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[Dict[str, float]]:
        values = self.calculate_series(high, low, close)
        return values[-1] if values else None

    def calculate_series(
        self, high: Sequence[float], low: Sequence[float], close: Sequence[float]
    ) -> List[Optional[Dict[str, float]]]:
        ci_series = ChoppinessIndex(self.period).calculate_series(high, low, close)
        output: List[Optional[Dict[str, float]]] = []
        for ci in ci_series:
            if ci is None:
                output.append(None)
                continue
            if ci >= self.choppy_threshold:
                regime = "choppy"
            elif ci <= self.trending_threshold:
                regime = "trending"
            else:
                regime = "balanced"
            output.append({"value": ci, "regime": regime})
        return output
