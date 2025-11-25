"""
Awesome Oscillator Indicator

The Awesome Oscillator is a momentum indicator that measures the difference between a fast and slow simple moving average of the median price.
"""

import numpy as np
from typing import List, Optional


class AwesomeOscillator:
    """
    Awesome Oscillator indicator.

    Formula:
    AO = SMA(fast_period, median_price) - SMA(slow_period, median_price)
    median_price = (high + low) / 2
    """

    def __init__(self, fast_period: int = 5, slow_period: int = 34):
        """
        Initialize Awesome Oscillator indicator.

        Args:
            fast_period: Fast SMA period (default: 5)
            slow_period: Slow SMA period (default: 34)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period

    def calculate(self, highs: List[float], lows: List[float]) -> Optional[float]:
        """
        Calculate Awesome Oscillator for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices

        Returns:
            AO value or None if insufficient data
        """
        if len(highs) < self.slow_period:
            return None

        # Calculate median prices
        median_prices = [(h + l) / 2 for h, l in zip(highs, lows)]

        # Calculate SMAs
        fast_sma = np.mean(median_prices[-self.fast_period:])
        slow_sma = np.mean(median_prices[-self.slow_period:])

        ao = fast_sma - slow_sma
        return ao

    def calculate_series(self, highs: List[float], lows: List[float]) -> List[Optional[float]]:
        """
        Calculate Awesome Oscillator for each point in the series.

        Args:
            highs: List of high prices
            lows: List of low prices

        Returns:
            List of AO values
        """
        ao_values = []
        for i in range(len(highs)):
            if i < self.slow_period - 1:
                ao_values.append(None)
            else:
                ao = self.calculate(highs[:i+1], lows[:i+1])
                ao_values.append(ao)
        return ao_values

    @staticmethod
    def get_signal(ao_current: float, ao_previous: float) -> str:
        """
        Get trading signal based on AO values.

        Args:
            ao_current: Current AO value
            ao_previous: Previous AO value

        Returns:
            Signal: 'bullish', 'bearish', or 'neutral'
        """
        if ao_current > ao_previous:
            return 'bullish'
        elif ao_current < ao_previous:
            return 'bearish'
        else:
            return 'neutral'
