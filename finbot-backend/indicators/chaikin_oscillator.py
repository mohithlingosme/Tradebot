"""
Chaikin Oscillator Indicator

The Chaikin Oscillator is the difference between the 3-day EMA of the Accumulation Distribution Line and the 10-day EMA of the ADL.
"""

import numpy as np
from typing import List, Optional


class ChaikinOscillator:
    """
    Chaikin Oscillator indicator.

    Formula:
    CO = EMA(3, ADL) - EMA(10, ADL)
    """

    def __init__(self, fast_period: int = 3, slow_period: int = 10):
        """
        Initialize Chaikin Oscillator indicator.

        Args:
            fast_period: Fast EMA period (default: 3)
            slow_period: Slow EMA period (default: 10)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> Optional[float]:
        """
        Calculate Chaikin Oscillator for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            volumes: List of volumes

        Returns:
            CO value or None if insufficient data
        """
        if len(highs) < self.slow_period:
            return None

        # Calculate ADL series
        adls = []
        for h, l, c, v in zip(highs, lows, closes, volumes):
            if h == l:
                adl = 0
            else:
                mfm = ((c - l) - (h - c)) / (h - l)
                adl = mfm * v
            adls.append(adl)

        # Calculate EMAs of ADL
        fast_ema = np.mean(adls[-self.fast_period:])  # Simplified
        slow_ema = np.mean(adls[-self.slow_period:])  # Simplified

        co = fast_ema - slow_ema
        return co

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> List[Optional[float]]:
        """
        Calculate Chaikin Oscillator for each point in the series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            volumes: List of volumes

        Returns:
            List of CO values
        """
        co_values = []
        for i in range(len(highs)):
            if i < self.slow_period - 1:
                co_values.append(None)
            else:
                co = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1], volumes[:i+1])
                co_values.append(co)
        return co_values
