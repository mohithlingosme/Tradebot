"""
Volume Weighted Average Price (VWAP) Indicator

VWAP calculates the average price weighted by volume, providing a benchmark
for intraday trading. It's commonly used to identify value levels.
"""

import numpy as np
from typing import List, Optional


class VWAP:
    """
    Volume Weighted Average Price (VWAP) indicator.

    Formula: VWAP = Σ(Price × Volume) / Σ(Volume)
    """

    def __init__(self):
        """Initialize VWAP indicator."""
        pass

    def calculate(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> Optional[float]:
        """
        Calculate VWAP for the given price and volume series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            volumes: List of volume values

        Returns:
            VWAP value or None if insufficient data
        """
        if len(highs) != len(lows) or len(lows) != len(closes) or len(closes) != len(volumes):
            return None

        if len(closes) == 0:
            return None

        # Calculate typical prices (can also use close, high, or other price types)
        typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]

        # Calculate VWAP
        price_volume_sum = sum(tp * vol for tp, vol in zip(typical_prices, volumes))
        volume_sum = sum(volumes)

        if volume_sum == 0:
            return None

        vwap = price_volume_sum / volume_sum

        return vwap

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> List[Optional[float]]:
        """
        Calculate VWAP for each point in the price series (cumulative).

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            volumes: List of volume values

        Returns:
            List of VWAP values
        """
        vwap_values = []
        for i in range(len(closes)):
            vwap = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1], volumes[:i+1])
            vwap_values.append(vwap)
        return vwap_values

    @staticmethod
    def get_signal(current_price: float, vwap_value: float) -> str:
        """
        Get trading signal based on price relative to VWAP.

        Args:
            current_price: Current price
            vwap_value: Current VWAP value

        Returns:
            Signal: 'above_vwap', 'below_vwap', or 'at_vwap'
        """
        if current_price > vwap_value:
            return 'above_vwap'
        elif current_price < vwap_value:
            return 'below_vwap'
        else:
            return 'at_vwap'
