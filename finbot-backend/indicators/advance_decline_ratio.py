"""
Advance Decline Ratio (ADR) Indicator

The Advance-Decline Ratio is a market breadth indicator that compares the number of advancing stocks to the number of declining stocks.
"""

import numpy as np
from typing import List, Optional


class AdvanceDeclineRatio:
    """
    Advance Decline Ratio (ADR) indicator.

    Formula:
    ADR = Advancing Issues / Declining Issues
    """

    def __init__(self):
        """
        Initialize ADR indicator.
        """
        pass

    def calculate(self, advancing: int, declining: int) -> Optional[float]:
        """
        Calculate ADR for a single period.

        Args:
            advancing: Number of advancing issues
            declining: Number of declining issues

        Returns:
            ADR value or None if declining is 0
        """
        if declining == 0:
            return None
        return advancing / declining

    def calculate_series(self, advancing_list: List[int], declining_list: List[int]) -> List[Optional[float]]:
        """
        Calculate ADR for each point in the series.

        Args:
            advancing_list: List of advancing issues
            declining_list: List of declining issues

        Returns:
            List of ADR values
        """
        adr_values = []
        for adv, dec in zip(advancing_list, declining_list):
            adr = self.calculate(adv, dec)
            adr_values.append(adr)
        return adr_values
