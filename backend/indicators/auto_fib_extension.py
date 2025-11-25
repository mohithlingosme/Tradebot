"""
Auto Fib Extension Indicator

The Auto Fib Extension automatically identifies Fibonacci extension levels based on recent price swings.
"""

import numpy as np
from typing import List, Optional, Dict


class AutoFibExtension:
    """
    Auto Fib Extension indicator.

    Identifies swing highs and lows to calculate Fibonacci extension levels.
    """

    def __init__(self, lookback: int = 50):
        """
        Initialize Auto Fib Extension indicator.

        Args:
            lookback: Lookback period for swing identification (default: 50)
        """
        self.lookback = lookback

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate Fibonacci extension levels.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices

        Returns:
            Dictionary of extension levels or None if insufficient data
        """
        if len(highs) < self.lookback:
            return None

        # Find recent swing high and low
        recent_highs = highs[-self.lookback:]
        recent_lows = lows[-self.lookback:]

        swing_high = max(recent_highs)
        swing_low = min(recent_lows)

        # Calculate Fibonacci extension levels (common ratios: 1.618, 2.618, 4.236)
        range_size = swing_high - swing_low

        extensions = {
            '161.8%': swing_low + range_size * 1.618,
            '261.8%': swing_low + range_size * 2.618,
            '423.6%': swing_low + range_size * 4.236
        }

        return extensions

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate extension levels for each point in the series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices

        Returns:
            List of extension level dictionaries
        """
        extension_values = []
        for i in range(len(highs)):
            if i < self.lookback - 1:
                extension_values.append(None)
            else:
                extensions = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                extension_values.append(extensions)
        return extension_values
