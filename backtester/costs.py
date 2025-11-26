from __future__ import annotations

from dataclasses import dataclass

from trading_engine.phase4.models import OrderSide


@dataclass
class CostModel:
    """Simple slippage + fees model suitable for event-based simulation."""

    slippage_bps: float = 1.0
    commission_rate: float = 0.0005
    fee_per_order: float = 0.0
    fee_per_unit: float = 0.0

    def price_with_slippage(self, side: OrderSide, price: float) -> float:
        if price <= 0:
            return price
        slip = (self.slippage_bps / 10_000) * price
        if side == OrderSide.BUY:
            return price + slip
        return price - slip

    def commission(self, price: float, quantity: float) -> float:
        return max(price * quantity * self.commission_rate, 0.0)

    def extra_fees(self, quantity: float) -> float:
        """Non-commission costs (e.g., exchange/broker fixed fees)."""
        return max(self.fee_per_order + self.fee_per_unit * quantity, 0.0)

    def total_fees(self, price: float, quantity: float) -> float:
        return self.commission(price, quantity) + self.extra_fees(quantity)
