from __future__ import annotations

"""Standardized signal dataclass used by strategies."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Literal, Optional


Action = Literal["BUY", "SELL", "CLOSE", "HOLD"]
OrderType = Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]


@dataclass(slots=True)
class Signal:
    """
    Canonical strategy signal representation.

    Example:
        Signal(action="BUY", symbol="INFY", price=1500.0, order_type="MARKET", qty=10)
    """

    action: Action
    symbol: str
    ts: datetime
    price: Optional[float] = None
    order_type: OrderType = "MARKET"
    qty: Optional[float] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export the signal as a serializable dictionary.
        """
        payload: Dict[str, Any] = {
            "action": self.action,
            "symbol": self.symbol,
            "price": self.price,
            "type": self.order_type,
            "ts": self.ts.isoformat(),
        }
        if self.qty is not None:
            payload["qty"] = self.qty
        if self.meta:
            payload["meta"] = self.meta
        return payload
