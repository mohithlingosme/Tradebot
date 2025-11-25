"""
Aroon Indicator

The Aroon indicator is used to identify trends and trend reversals.
"""

import numpy as np
from typing import List, Optional, Dict


class Aroon:
    """
    Aroon indicator.

    Formula:
    Aroon Up = ((period - periods since high) / period) * 100
    Aroon Down = ((period - periods since low) / period) * 100
    """

    def __init__(self, period: int = 14):
        """
        Initialize Aroon indicator.

        Args:
            period: Lookback period (default: 14)
        """
        self.period = period

    def calculate(self, highs: List[float], lows: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate Aroon for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices

        Returns:
            Dictionary with aroon_up and aroon_down or None if insufficient data
        """
        if len(highs) < self.period or len(lows) < self.period:
            return None

        # Calculate periods since highest high and lowest low
        recent_highs = highs[-self.period:]
        recent_lows = lows[-self.period:]

        periods_since_high = self.period - (np.argmax(recent_highs) + 1)
        periods_since_low = self.period - (np.argmin(recent_lows) + 1)

        aroon_up = (periods_since_high / self.period) * 100
        aroon_down = (periods_since_low / self.period) * 100

        return {
            'aroon_up': aroon_up,
            'aroon_down': aroon_down
        }

    def calculate_series(self, highs: List[float], lows: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate Aroon for each point in the series.

        Args:
            highs: List of high prices
            lows: List of low prices

        Returns:
            List of Aroon dictionaries
        """
        aroon_values = []
        for i in range(len(highs)):
            if i < self.period - 1:
                aroon_values.append(None)
            else:
                aroon = self.calculate(highs[:i+1], lows[:i+1])
                aroon_values.append(aroon)
        return aroon_values

    @staticmethod
    def get_signal(aroon_up: float, aroon_down: float) -> str:
        """
        Get trading signal based on Aroon values.

        Args:
            aroon_up: Aroon Up value
            aroon_down: Aroon Down value

        Returns:
            Signal: 'bullish', 'bearish', or 'neutral'
        """
        if aroon_up > 70 and aroon_down < 30:
            return 'bullish'
        elif aroon_down > 70 and aroon_up < 30:
            return 'bearish'
        else:
            return 'neutral'
