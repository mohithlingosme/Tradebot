"""
Advance Decline Line (ADL) Indicator

The Advance Decline Line is a breadth indicator that plots the difference between advancing and declining stocks.
"""

import numpy as np
from typing import List, Optional


class AdvanceDeclineLine:
    """
    Advance Decline Line (ADL) indicator.

    Formula:
    ADL = Previous ADL + (Advancing Issues - Declining Issues)
    """

    def __init__(self):
        """
        Initialize ADL indicator.
        """
        pass

    def calculate(self, advancing: int, declining: int, prev_adl: float) -> float:
        """
        Calculate ADL for a single period.

        Args:
            advancing: Number of advancing issues
            declining: Number of declining issues
            prev_adl: Previous ADL value

        Returns:
            Current ADL value
        """
        adl = prev_adl + (advancing - declining)
        return adl

    def calculate_series(self, advancing_list: List[int], declining_list: List[int]) -> List[float]:
        """
        Calculate ADL for each point in the series.

        Args:
            advancing_list: List of advancing issues
            declining_list: List of declining issues

        Returns:
            List of ADL values
        """
        adl_values = []
        prev_adl = 0.0
        for adv, dec in zip(advancing_list, declining_list):
            adl = self.calculate(adv, dec, prev_adl)
            adl_values.append(adl)
            prev_adl = adl
        return adl_values
