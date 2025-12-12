"""
Simple seasonality score.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, List, Optional, Sequence


@dataclass
class Seasonality:
    """Compare current period returns with the historical average for the same cycle slot."""

    cycle_length: int = 20

    def calculate(self, close: Sequence[float]) -> Optional[Dict[str, float]]:
        values = self.calculate_series(close)
        return values[-1] if values else None

    def calculate_series(self, close: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        closes = list(float(v) for v in close)
        output: List[Optional[Dict[str, float]]] = []
        if len(closes) <= self.cycle_length:
            return [None] * len(closes)
        bucket_returns: Dict[int, List[float]] = {i: [] for i in range(self.cycle_length)}
        for idx in range(self.cycle_length, len(closes)):
            bucket = idx % self.cycle_length
            past_price = closes[idx - self.cycle_length]
            if past_price == 0:
                continue
            ret = (closes[idx] / past_price) - 1.0
            bucket_returns[bucket].append(ret)
            avg = mean(bucket_returns[bucket]) if bucket_returns[bucket] else 0.0
            score = ret - avg
            output.append({"bucket": bucket, "return": ret, "avg": avg, "score": score})
        return [None] * (len(closes) - len(output)) + output
