"""
Williams %R Indicator

Williams %R is a momentum indicator that measures overbought and oversold levels.
Similar to Stochastic Oscillator but uses a different calculation method.
"""

import numpy as np
from typing import List, Optional


class WilliamsR:
    """
    Williams %R indicator.

    Formula: %R = (Highest High - Close) / (Highest High - Lowest Low) × (-100)
    Range: -100 to 0 (most oversold at -100, most overbought at 0)
    """

    def __init__(self, period: int = 14):
        """
        Initialize Williams %R indicator.

        Args:
            period: Lookback period (default: 14)
        """
        self.period = period

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[float]:
        """
        Calculate Williams %R for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            Williams %R value (-100 to 0) or None if insufficient data
        """
        if len(highs) < self.period or len(lows) < self.period or len(closes) < self.period:
            return None

        highest_high = max(highs[-self.period:])
        lowest_low = min(lows[-self.period:])
        current_close = closes[-1]

        if highest_high == lowest_low:
            return -50.0  # Neutral when no range

        williams_r = ((highest_high - current_close) / (highest_high - lowest_low)) * (-100)

        return williams_r

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[float]]:
        """
        Calculate Williams %R for each point in the price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            List of Williams %R values
        """
        williams_values = []
        for i in range(len(closes)):
            if i < self.period - 1:
                williams_values.append(None)
            else:
                williams_r = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                williams_values.append(williams_r)
        return williams_values

    @staticmethod
    def get_signal(williams_r_value: float, overbought: float = -20, oversold: float = -80) -> str:
        """
        Get trading signal based on Williams %R value.

        Args:
            williams_r_value: Current Williams %R value
            overbought: Overbought threshold (default: -20)
            oversold: Oversold threshold (default: -80)

        Returns:
            Signal: 'overbought', 'oversold', or 'neutral'
        """
        if williams_r_value >= overbought:
            return 'overbought'
        elif williams_r_value <= oversold:
            return 'oversold'
        else:
            return 'neutral'
