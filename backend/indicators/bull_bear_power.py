"""
Bull Bear Power Indicator

The Bull Bear Power indicator measures the strength of bulls versus bears.
"""

import numpy as np
from typing import Dict, List, Optional


class BullBearPower:
    """
    Bull Bear Power indicator.

    Formula:
    Bull Power = High - EMA
    Bear Power = Low - EMA
    """

    def __init__(self, period: int = 13):
        """
        Initialize Bull Bear Power indicator.

        Args:
            period: EMA period (default: 13)
        """
        self.period = period

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate Bull Bear Power for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices

        Returns:
            Dictionary with bull_power and bear_power or None if insufficient data
        """
        if len(closes) < self.period:
            return None

        # Calculate EMA of closes
        ema = np.mean(closes[-self.period:])  # Simplified EMA

        # Calculate powers
        high = highs[-1]
        low = lows[-1]

        bull_power = high - ema
        bear_power = low - ema

        return {
            'bull_power': bull_power,
            'bear_power': bear_power
        }

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate Bull Bear Power for each point in the series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices

        Returns:
            List of Bull Bear Power dictionaries
        """
        power_values = []
        for i in range(len(highs)):
            if i < self.period - 1:
                power_values.append(None)
            else:
                power = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                power_values.append(power)
        return power_values
