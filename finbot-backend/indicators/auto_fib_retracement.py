"""
Auto Fib Retracement Indicator

The Auto Fib Retracement automatically identifies Fibonacci retracement levels based on recent price swings.
"""

import numpy as np
from typing import List, Optional, Dict


class AutoFibRetracement:
    """
    Auto Fib Retracement indicator.

    Identifies swing highs and lows to calculate Fibonacci retracement levels.
    """

    def __init__(self, lookback: int = 50):
        """
        Initialize Auto Fib Retracement indicator.

        Args:
            lookback: Lookback period for swing identification (default: 50)
        """
        self.lookback = lookback

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate Fibonacci retracement levels.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices

        Returns:
            Dictionary of retracement levels or None if insufficient data
        """
        if len(highs) < self.lookback:
            return None

        # Find recent swing high and low
        recent_highs = highs[-self.lookback:]
        recent_lows = lows[-self.lookback:]

        swing_high = max(recent_highs)
        swing_low = min(recent_lows)

        # Calculate Fibonacci retracement levels (common ratios: 0.236, 0.382, 0.5, 0.618, 0.786)
        range_size = swing_high - swing_low

        retracements = {
            '23.6%': swing_high - range_size * 0.236,
            '38.2%': swing_high - range_size * 0.382,
            '50.0%': swing_high - range_size * 0.5,
            '61.8%': swing_high - range_size * 0.618,
            '78.6%': swing_high - range_size * 0.786
        }

        return retracements

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate retracement levels for each point in the series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices

        Returns:
            List of retracement level dictionaries
        """
        retracement_values = []
        for i in range(len(highs)):
            if i < self.lookback - 1:
                retracement_values.append(None)
            else:
                retracements = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                retracement_values.append(retracements)
        return retracement_values
