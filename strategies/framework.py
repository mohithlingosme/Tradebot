import abc
from typing import TypedDict, Dict, Any
from dataclasses import dataclass
from datetime import datetime


class Signal(TypedDict):
    action: str  # 'BUY' or 'SELL'
    symbol: str
    price: float
    type: str  # 'LIMIT' or 'MARKET'
    metadata: Dict[str, Any]


@dataclass
class MarketData:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Strategy(abc.ABC):
    def __init__(self, symbol: str, params: Dict[str, Any]):
        self.symbol = symbol
        self.params = params

    @abc.abstractmethod
    def initialize(self) -> None:
        """Initialize indicators and setup."""
        pass

    @abc.abstractmethod
    def next(self, candle: MarketData) -> None:
        """Process each candle and generate signals."""
        pass

    def create_signal(self, action: str, price: float, type: str = 'LIMIT', metadata: Dict[str, Any] = None) -> Signal:
        """Helper method to create a standardized signal."""
        if metadata is None:
            metadata = {}
        return Signal(
            action=action,
            symbol=self.symbol,
            price=price,
            type=type,
            metadata=metadata
        )
