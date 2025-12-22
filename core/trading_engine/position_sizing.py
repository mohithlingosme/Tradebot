"""
Position sizing helpers.
"""

from __future__ import annotations

from typing import Optional

from .models import PortfolioState, Signal


class PositionSizer:
    """Simple sizing rules: fixed fraction of equity and risk-per-trade."""

    def __init__(self, equity_fraction: float = 0.02, risk_per_trade: float = 0.01):
        self.equity_fraction = equity_fraction
        self.risk_per_trade = risk_per_trade

    def size_order(
        self,
        signal: Signal,
        price: float,
        portfolio: PortfolioState,
        stop_loss: Optional[float] = None,
    ) -> float:
        if signal.size is not None:
            return signal.size

        equity = portfolio.equity
        fixed_fraction_qty = (equity * self.equity_fraction) / price if price > 0 else 0.0

        if stop_loss is None or stop_loss >= price:
            return max(fixed_fraction_qty, 0.0)

        risk_per_unit = price - stop_loss
        risk_based_qty = (equity * self.risk_per_trade) / risk_per_unit if risk_per_unit > 0 else 0.0

        # Use the more conservative of the two sizing methods
        if risk_based_qty <= 0:
            return max(fixed_fraction_qty, 0.0)
        if fixed_fraction_qty <= 0:
            return max(risk_based_qty, 0.0)
        return max(min(fixed_fraction_qty, risk_based_qty), 0.0)
