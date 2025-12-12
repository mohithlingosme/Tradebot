"""
Price envelope indicator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from .utils import sma


@dataclass
class Envelope:
    """Bands built around a moving average with a configurable percentage offset."""

    period: int = 20
    pct: float = 2.5

    def calculate(self, close: Sequence[float]) -> Optional[Dict[str, float]]:
        mean = sma(close, self.period)
        if mean is None:
            return None
        upper = mean * (1 + self.pct / 100.0)
        lower = mean * (1 - self.pct / 100.0)
        return {"upper": upper, "middle": mean, "lower": lower}

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        output: List[Optional[Dict[str, float]]] = []
        for i in range(len(close)):
            output.append(self.calculate(close[: i + 1]))
        return output
