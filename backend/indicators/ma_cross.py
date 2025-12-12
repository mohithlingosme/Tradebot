"""
Moving average crossover helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from .moving_average import EMA, SMA


@dataclass
class MovingAverageCross:
    """Generate bull/bear signals when fast MA crosses a slow MA."""

    fast_period: int = 12
    slow_period: int = 26
    use_exponential: bool = True

    def _ma(self, period: int):
        return EMA(period) if self.use_exponential else SMA(period)

    def calculate(self, close: Sequence[float]) -> Optional[str]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[str]]:
        fast_ma = self._ma(self.fast_period)
        slow_ma = self._ma(self.slow_period)
        signals: List[Optional[str]] = []
        prev_relation: Optional[str] = None
        for idx in range(len(close)):
            fast_value = fast_ma.calculate(list(close[: idx + 1]))
            slow_value = slow_ma.calculate(list(close[: idx + 1]))
            if fast_value is None or slow_value is None:
                signals.append(None)
                continue
            if fast_value > slow_value:
                relation = "above"
            elif fast_value < slow_value:
                relation = "below"
            else:
                relation = "equal"
            signal = None
            if prev_relation == "below" and relation == "above":
                signal = "bullish_cross"
            elif prev_relation == "above" and relation == "below":
                signal = "bearish_cross"
            signals.append(signal)
            prev_relation = relation
        return signals
