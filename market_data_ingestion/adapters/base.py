from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional


@dataclass
class OrderBookLevel:
    price: float
    size: float

    def to_dict(self) -> Dict[str, float]:
        return {"price": self.price, "size": self.size}


@dataclass
class NormalizedTick:
    """Canonical tick structure used across providers."""

    symbol: str
    ts_utc: datetime
    price: float
    volume: float
    provider: str
    raw: Dict[str, Any]
    bids: Optional[List[OrderBookLevel]] = None
    asks: Optional[List[OrderBookLevel]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["ts_utc"] = self.ts_utc.isoformat()
        if self.bids is not None:
            data["bids"] = [level.to_dict() for level in self.bids]
        if self.asks is not None:
            data["asks"] = [level.to_dict() for level in self.asks]
        return data


class BaseMarketDataAdapter(abc.ABC):
    """Abstract base class for market data adapters."""

    provider: str = "unknown"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connected = False
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._connected

    @abc.abstractmethod
    async def connect(self) -> None:
        ...

    @abc.abstractmethod
    async def close(self) -> None:
        ...

    @abc.abstractmethod
    async def subscribe(self, symbols: List[str]) -> None:
        ...

    @abc.abstractmethod
    async def stream(self) -> AsyncGenerator[NormalizedTick, None]:
        """Yield normalized ticks."""
        ...

    async def _mark_connected(self, state: bool) -> None:
        async with self._lock:
            self._connected = state

    def _normalize_price(self, price: Any) -> float:
        try:
            return float(price)
        except Exception:
            return 0.0

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
