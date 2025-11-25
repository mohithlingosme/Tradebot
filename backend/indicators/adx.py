"""
Average Directional Index (ADX) Indicator

ADX measures the strength of a trend, regardless of its direction.
It is derived from the Directional Movement System.
"""

import numpy as np
from typing import List, Optional, Dict


class ADX:
    """
    Average Directional Index (ADX) indicator.

    Components:
    - +DI: Positive Directional Indicator
    - -DI: Negative Directional Indicator
    - ADX: Average Directional Index
    """

    def __init__(self, period: int = 14):
        """
        Initialize ADX indicator.

        Args:
            period: Lookback period (default: 14)
        """
        self.period = period

    def calculate(self, highs: List[float], lows: List[float], closes: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate ADX for the given price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            Dictionary with ADX components or None if insufficient data
        """
        if len(highs) < self.period + 1 or len(lows) < self.period + 1 or len(closes) < self.period + 1:
            return None

        # Calculate True Range and Directional Movement
        tr_values = []
        plus_dm_values = []
        minus_dm_values = []

        for i in range(1, len(highs)):
            # True Range
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_values.append(tr)

            # Directional Movement
            move_up = highs[i] - highs[i-1]
            move_down = lows[i-1] - lows[i]

            plus_dm = move_up if move_up > move_down and move_up > 0 else 0
            minus_dm = move_down if move_down > move_up and move_down > 0 else 0

            plus_dm_values.append(plus_dm)
            minus_dm_values.append(minus_dm)

        if len(tr_values) < self.period:
            return None

        # Calculate smoothed averages
        avg_tr = np.mean(tr_values[-self.period:])
        avg_plus_dm = np.mean(plus_dm_values[-self.period:])
        avg_minus_dm = np.mean(minus_dm_values[-self.period:])

        # Calculate Directional Indicators
        plus_di = (avg_plus_dm / avg_tr) * 100 if avg_tr != 0 else 0
        minus_di = (avg_minus_dm / avg_tr) * 100 if avg_tr != 0 else 0

        # Calculate DX and ADX
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100 if (plus_di + minus_di) != 0 else 0

        # For simplicity, using DX as ADX for the current calculation
        # In practice, ADX is smoothed over time
        adx = dx

        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di,
            'dx': dx
        }

    def calculate_series(self, highs: List[float], lows: List[float], closes: List[float]) -> List[Optional[Dict[str, float]]]:
        """
        Calculate ADX for each point in the price series.

        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices

        Returns:
            List of ADX dictionaries
        """
        adx_values = []
        for i in range(len(closes)):
            if i < self.period:
                adx_values.append(None)
            else:
                adx = self.calculate(highs[:i+1], lows[:i+1], closes[:i+1])
                adx_values.append(adx)
        return adx_values

    @staticmethod
    def get_signal(adx_data: Dict[str, float], trend_threshold: float = 25) -> str:
        """
        Get trading signal based on ADX value.

        Args:
            adx_data: ADX calculation result
            trend_threshold: Trend strength threshold (default: 25)

        Returns:
            Signal: 'strong_trend', 'weak_trend', or 'sideways'
        """
        adx = adx_data['adx']

        if adx >= trend_threshold:
            return 'strong_trend'
        else:
            return 'weak_trend'
