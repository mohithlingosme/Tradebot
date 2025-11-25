"""
BBTrend Indicator

The BBTrend indicator combines Bollinger Bands with trend analysis.
"""

import numpy as np
from typing import List, Optional, Dict


class BBTrend:
    """
    BBTrend indicator.

    Combines Bollinger Bands with trend direction.
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        Initialize BBTrend indicator.

        Args:
            period: Period for Bollinger Bands (default: 20)
            std_dev: Standard deviation multiplier (default: 2.0)
        """
        self.period = period
        self.std_dev = std_dev

    def calculate(self, closes: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate BBTrend for the given price series.

        Args:
            closes: List of close prices

        Returns:
            Dictionary with trend and BB data or None if insufficient data
        """
        if len(closes) < self.period:
            return None

        # Calculate Bollinger Bands
        recent_closes = closes[-self.period:]
        sma = np.mean(recent_closes)
        std = np.std(recent_closes)
        upper_band = sma + self.std_dev * std
        lower_band = sma - self.std_dev * std

        # Simple trend: compare current close to SMA
        current_close = closes[-1]
        trend = 'up' if current_close > sma else 'down'

        return {
            'trend': trend,
            'upper_band': upper_band,
            'middle_band': sma,
            'lower_band': lower_band,
            'bandwidth': (upper_band - lower_band) / sma
        }

    def calculate_series(self, closes: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate BBTrend for each point in the series.

        Args:
            closes: List of close prices

        Returns:
            List of BBTrend dictionaries
        """
        bbtrend_values = []
        for i in range(len(closes)):
            if i < self.period - 1:
                bbtrend_values.append(None)
            else:
                bbtrend = self.calculate(closes[:i+1])
                bbtrend_values.append(bbtrend)
        return bbtrend_values
