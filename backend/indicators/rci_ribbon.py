"""
RCI ribbon combining multiple lookbacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .rank_correlation_index import _rci


@dataclass
class RCIRibbon:
    """Return RCI values for several lookbacks to mimic ribbon visualization."""

    periods: List[int] = field(default_factory=lambda: [9, 26, 52])

    def calculate(self, close: Sequence[float]) -> Optional[Dict[int, float]]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[int, float]]]:
        output: List[Optional[Dict[int, float]]] = []
        for i in range(len(close)):
            snapshot: Dict[int, float] = {}
            for period in self.periods:
                if i + 1 >= period:
                    snapshot[period] = _rci(close[i - period + 1 : i + 1])
            output.append(snapshot if snapshot else None)
        return output
