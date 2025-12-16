from __future__ import annotations

"""Canonical strategy interface shared across trading flows."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from common.market_data import Candle

Signal = Dict[str, Any]


class Strategy(ABC):
    """Base class for trading strategies with internal state management."""

    def __init__(self, data_feed):
        self.data_feed = data_feed
        self.state: Dict[str, Any] = {}

    @abstractmethod
    def next(self) -> Signal:
        """Process the latest data and return a trading signal.

        Returns:
            Signal: Standardized signal format {'action': 'BUY', 'symbol': 'INFY', 'price': 1500, 'type': 'LIMIT'}.
        """
        pass
