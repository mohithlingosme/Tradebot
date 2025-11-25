"""
Accumulation / Distribution (A/D) Indicator

The Accumulation/Distribution indicator is a volume-based indicator designed to measure the cumulative flow of money into and out of a security.
"""

import numpy as np
from typing import List, Optional


class AccumulationDistribution:
    """
    Accumulation / Distribution (A/D) indicator.

    Formula:
    CLV = [(Close - Low) - (High - Close)] / (High - Low)
    A/D = Previous A/D + CLV * Volume
    """

    def __init__(self):
        """
        Initialize A/D indicator.
        """
        pass

    def calculate(self, high: float, low: float, close: float, volume: float, prev_ad: float) -> float:
        """
        Calculate A/D for a single period.

        Args:
            high: High price
            low: Low price
            close: Close price
            volume: Volume
            prev_ad: Previous A/D value

        Returns:
            Current A/D value
        """
        if high == low:
            clv = 0
        else:
            clv = ((close - low) - (high - close)) / (high - low)
        ad = prev_ad + clv * volume
        return ad

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> List[float]:
        """
        Calculate A/D for each point in the series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            volumes: List of volumes

        Returns:
            List of A/D values
        """
        ad_values = []
        prev_ad = 0.0
        for h, l, c, v in zip(highs, lows, closes, volumes):
            ad = self.calculate(h, l, c, v, prev_ad)
            ad_values.append(ad)
            prev_ad = ad
        return ad_values
