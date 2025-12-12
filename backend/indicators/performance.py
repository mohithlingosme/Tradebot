"""
Performance indicator: percent return over configurable lookbacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


@dataclass
class Performance:
    """Compute cumulative returns across multiple lookbacks."""

    lookbacks: List[int] = field(default_factory=lambda: [5, 20, 60])

    def calculate(self, close: Sequence[float]) -> Optional[Dict[int, float]]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[int, float]]]:
        closes = list(float(v) for v in close)
        results: List[Optional[Dict[int, float]]] = []
        for idx in range(len(closes)):
            snapshot: Dict[int, float] = {}
            for lb in self.lookbacks:
                if idx < lb:
                    continue
                base = closes[idx - lb]
                if base != 0:
                    snapshot[lb] = (closes[idx] / base) - 1.0
            results.append(snapshot if snapshot else None)
        return results
