"""
Auto Trendlines Indicator

The Auto Trendlines automatically identifies and draws trendlines based on pivot points.
"""

import numpy as np
from typing import List, Optional, Dict


class AutoTrendlines:
    """
    Auto Trendlines indicator.

    Identifies pivot points to draw trendlines.
    """

    def __init__(self, lookback: int = 50):
        """
        Initialize Auto Trendlines indicator.

        Args:
            lookback: Lookback period for pivot identification (default: 50)
        """
        self.lookback = lookback

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict[str, List[float]]]:
        """
        Calculate trendline levels.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices

        Returns:
            Dictionary of trendlines or None if insufficient data
        """
        if len(highs) < self.lookback:
            return None

        # Simple implementation: connect recent highs and lows
        recent_highs = highs[-self.lookback:]
        recent_lows = lows[-self.lookback:]

        # Find two recent highs and two recent lows
        high1 = max(recent_highs[:len(recent_highs)//2])
        high2 = max(recent_highs[len(recent_highs)//2:])
        low1 = min(recent_lows[:len(recent_lows)//2])
        low2 = min(recent_lows[len(recent_lows)//2:])

        # Calculate trendlines (simplified linear interpolation)
        resistance = [high1 + (high2 - high1) * (i / (len(highs) - 1)) for i in range(len(highs))]
        support = [low1 + (low2 - low1) * (i / (len(lows) - 1)) for i in range(len(lows))]

        trendlines = {
            'resistance': resistance,
            'support': support
        }

        return trendlines

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[Dict[str, List[float]]]]:
        """
        Calculate trendlines for each point in the series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices

        Returns:
            List of trendline dictionaries
        """
        trendline_values = []
        for i in range(len(highs)):
            if i < self.lookback - 1:
                trendline_values.append(None)
            else:
                trendlines = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                trendline_values.append(trendlines)
        return trendline_values
