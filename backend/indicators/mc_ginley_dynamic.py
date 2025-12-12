"""
McGinley Dynamic indicator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class McGinleyDynamic:
    """Adaptive moving average that contracts/expands with volatility."""

    period: int = 14

    def calculate(self, close: Sequence[float]) -> Optional[float]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[float]]:
        prices = list(float(v) for v in close)
        if not prices:
            return []
        output: List[Optional[float]] = [None] * len(prices)
        avg = sum(prices[: self.period]) / self.period if len(prices) >= self.period else prices[0]
        for idx, price in enumerate(prices):
            if idx == 0:
                avg = price
                output[idx] = avg
                continue
            ratio = price / avg if avg != 0 else 1.0
            avg = avg + (price - avg) / (self.period * (ratio ** 4))
            output[idx] = avg
        return output
