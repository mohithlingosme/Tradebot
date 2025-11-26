from __future__ import annotations

from typing import List, Optional

from trading_engine.phase4.models import (
    Bar,
    OrderFill,
    OrderRequest,
    OrderSide,
    OrderStatus,
    PortfolioState,
)
from trading_engine.phase4.paper_engine import PaperTradingEngine

from .costs import CostModel


class TradeSimulator:
    """Wraps the paper engine with explicit fee/slippage accounting."""

    def __init__(self, cost_model: CostModel, portfolio: Optional[PortfolioState] = None):
        self.cost_model = cost_model
        self.paper_engine = PaperTradingEngine(
            portfolio=portfolio or PortfolioState(cash=100_000.0, daily_start_equity=None),
            slippage_bps=cost_model.slippage_bps,
            commission_rate=cost_model.commission_rate,
        )
        if self.paper_engine.portfolio.daily_start_equity is None:
            self.paper_engine.portfolio.daily_start_equity = self.paper_engine.portfolio.equity
        self.fees_paid = 0.0

    @property
    def portfolio(self) -> PortfolioState:
        return self.paper_engine.portfolio

    def mark_to_market(self, bar: Bar) -> List[OrderFill]:
        fills = self.paper_engine.update_mark_to_market(bar)
        for fill in fills:
            self._apply_costs(fill)
        return fills

    def execute(self, order: OrderRequest, bar: Bar) -> OrderFill:
        fill = self.paper_engine.execute_order(order, bar)
        self._apply_costs(fill)
        return fill

    def _apply_costs(self, fill: OrderFill) -> None:
        """Add post-trade fees and adjust P&L to net values."""
        if fill.status not in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED):
            return
        if fill.filled_quantity <= 0:
            return

        commission = self.cost_model.commission(fill.fill_price, fill.filled_quantity)
        extra = self.cost_model.extra_fees(fill.filled_quantity)
        total = commission + extra
        if extra:
            self.paper_engine.portfolio.cash -= extra
        if total:
            self.paper_engine.portfolio.realized_pnl -= total
            fill.pnl -= total
            self.fees_paid += total
