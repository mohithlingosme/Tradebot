from __future__ import annotations

"""Canonical strategy interface shared across trading flows."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Literal

from common.market_data import Candle

Signal = Literal["BUY", "SELL", "HOLD"]


class Strategy(ABC):
    """Base class for trading strategies with internal state management."""

    def __init__(self):
        self.state: Dict[str, Any] = {}

    @abstractmethod
    def on_bar(self, bar: Candle, state: Dict[str, Any]) -> Signal:
        """Process a new bar and return a trading signal.

        Args:
            bar: Normalized OHLCV candle (`common.market_data.Candle`).
            state: Mutable dictionary representing the strategy's working state.
                Implementations may store derived indicator values or any other
                metadata either on `self` or inside this dictionary.

        Returns:
            Signal: Typically `'BUY'`, `'SELL'`, or `'HOLD'`. Implementations can
            optionally return a richer signal object/dataclass if downstream
            consumers expect additional metadata (stop loss, take profit, etc.).
        """
        pass
