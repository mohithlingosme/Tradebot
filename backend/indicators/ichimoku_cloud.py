"""
Ichimoku Cloud Indicator

A comprehensive trend-following indicator with multiple lines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np


@dataclass
class IchimokuCloud:
    """Ichimoku Cloud indicator."""

    tenkan_period: int = 9
    kijun_period: int = 26
    senkou_span_b_period: int = 52
    displacement: int = 26

    def calculate(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> Optional[Dict[str, float]]:
        """Return the Ichimoku components for the latest period."""
        if len(high) < self.senkou_span_b_period or len(low) < self.senkou_span_b_period or len(close) < self.senkou_span_b_period:
            return None

        # Tenkan-sen (Conversion Line)
        tenkan_high = np.max(high[-self.tenkan_period:])
        tenkan_low = np.min(low[-self.tenkan_period:])
        tenkan_sen = (tenkan_high + tenkan_low) / 2

        # Kijun-sen (Base Line)
        kijun_high = np.max(high[-self.kijun_period:])
        kijun_low = np.min(low[-self.kijun_period:])
        kijun_sen = (kijun_high + kijun_low) / 2

        # Senkou Span A (Leading Span A)
        senkou_span_a = (tenkan_sen + kijun_sen) / 2

        # Senkou Span B (Leading Span B)
        senkou_high = np.max(high[-self.senkou_span_b_period:])
        senkou_low = np.min(low[-self.senkou_span_b_period:])
        senkou_span_b = (senkou_high + senkou_low) / 2

        # Chikou Span (Lagging Span)
        chikou_span = close[-self.displacement]

        return {
            'tenkan_sen': float(tenkan_sen),
            'kijun_sen': float(kijun_sen),
            'senkou_span_a': float(senkou_span_a),
            'senkou_span_b': float(senkou_span_b),
            'chikou_span': float(chikou_span)
        }

    def calculate_series(self, high: Sequence[float], low: Sequence[float], close: Sequence[float]) -> List[Optional[Dict[str, float]]]:
        """Return Ichimoku series."""
        ichimoku = []
        for i in range(len(close)):
            if i < self.senkou_span_b_period - 1:
                ichimoku.append(None)
            else:
                # Simplified calculation
                tenkan_high = np.max(high[i - self.tenkan_period + 1 : i + 1])
                tenkan_low = np.min(low[i - self.tenkan_period + 1 : i + 1])
                tenkan_sen = (tenkan_high + tenkan_low) / 2

                kijun_high = np.max(high[i - self.kijun_period + 1 : i + 1])
                kijun_low = np.min(low[i - self.kijun_period + 1 : i + 1])
                kijun_sen = (kijun_high + kijun_low) / 2

                senkou_span_a = (tenkan_sen + kijun_sen) / 2

                senkou_high = np.max(high[i - self.senkou_span_b_period + 1 : i + 1])
                senkou_low = np.min(low[i - self.senkou_span_b_period + 1 : i + 1])
                senkou_span_b = (senkou_high + senkou_low) / 2

                chikou_idx = i - self.displacement
                chikou_span = close[chikou_idx] if chikou_idx >= 0 else None

                ichimoku.append({
                    'tenkan_sen': float(tenkan_sen),
                    'kijun_sen': float(kijun_sen),
                    'senkou_span_a': float(senkou_span_a),
                    'senkou_span_b': float(senkou_span_b),
                    'chikou_span': chikou_span
                })
        return ichimoku
