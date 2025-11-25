"""
Change Momentum Oscillator Indicator

The Change Momentum Oscillator measures the rate of change of momentum.
"""

import numpy as np
from typing import List, Optional


class ChangeMomentumOscillator:
    """
    Change Momentum Oscillator indicator.

    Formula:
    CMO = (UpSum - DownSum) / (UpSum + DownSum) * 100
    where UpSum is sum of up moves, DownSum is sum of down moves
    """

    def __init__(self, period: int = 14):
        """
        Initialize Change Momentum Oscillator indicator.

        Args:
            period: Lookback period (default: 14)
        """
        self.period = period

    def calculate(self, closes: List[float]) -> Optional[float]:
        """
        Calculate CMO for the given price series.

        Args:
            closes: List of close prices

        Returns:
            CMO value (-100 to 100) or None if insufficient data
        """
        if len(closes) < self.period + 1:
            return None

        # Calculate price changes
        deltas = np.diff(closes[-self.period-1:])

        # Separate up and down moves
        ups = np.where(deltas > 0, deltas, 0)
        downs = np.where(deltas < 0, -deltas, 0)

        up_sum = np.sum(ups)
        down_sum = np.sum(downs)

        if up_sum + down_sum == 0:
            return 0.0

        cmo = ((up_sum - down_sum) / (up_sum + down_sum)) * 100
        return cmo

    def calculate_series(self, closes: List[float]) -> List[Optional[float]]:
        """
        Calculate CMO for each point in the series.

        Args:
            closes: List of close prices

        Returns:
            List of CMO values
        """
        cmo_values = []
        for i in range(len(closes)):
            if i < self.period:
                cmo_values.append(None)
            else:
                cmo = self.calculate(closes[:i+1])
                cmo_values.append(cmo)
        return cmo_values

    @staticmethod
    def get_signal(cmo_value: float, overbought: float = 50, oversold: float = -50) -> str:
        """
        Get trading signal based on CMO value.

        Args:
            cmo_value: Current CMO value
            overbought: Overbought threshold (default: 50)
            oversold: Oversold threshold (default: -50)

        Returns:
            Signal: 'overbought', 'oversold', or 'neutral'
        """
        if cmo_value >= overbought:
            return 'overbought'
        elif cmo_value <= oversold:
            return 'oversold'
        else:
            return 'neutral'
