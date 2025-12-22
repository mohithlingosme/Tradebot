from __future__ import annotations

"""
Lightweight risk engine for backtests and paper trading.

This module focuses on simple capital-based limits (risk per trade, daily loss,
lot-size bounds, trade counts). It is intentionally narrower than
`risk/risk_manager.py`, which targets live trading integrations.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class RiskEngine:
    capital: float
    max_risk_per_trade: float = 0.01  # 1% of capital
    max_daily_loss: float = 0.03      # 3% drawdown
    max_lot_size: float = 10.0
    max_trades_per_day: int = 20
    sl_range: tuple[float, float] = (0.001, 0.1)  # min/max % distance
    tp_range: tuple[float, float] = (0.001, 0.2)
    current_day_pnl: float = 0.0
    trade_count_today: int = 0
    current_day: date = field(default_factory=date.today)

    def _reset_if_new_day(self) -> None:
        today = date.today()
        if today != self.current_day:
            self.current_day = today
            self.current_day_pnl = 0.0
            self.trade_count_today = 0

    def can_open_trade(self, size: float, stop_distance: float, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> bool:
        """
        Determine if a trade can be opened given sizing, SL distance, and daily limits.

        Args:
            size: Proposed position size (lots/shares).
            stop_distance: Monetary risk per share/contract (price - stop).
            stop_loss: Optional stop percentage.
            take_profit: Optional take-profit percentage.
        """
        self._reset_if_new_day()
        if self.check_daily_limit():
            return False
        if self.trade_count_today >= self.max_trades_per_day:
            return False
        if size > self.max_lot_size:
            return False
        if stop_distance <= 0:
            return False

        per_trade_risk = size * stop_distance
        max_lot_scale = max(1.0, float(self.max_lot_size))
        size_fraction = min(size / max_lot_scale, 1.0)
        # Distribute the total per-trade risk budget across the configured lot allowance
        allowed_risk = (self.capital * self.max_risk_per_trade) * size_fraction
        if per_trade_risk >= allowed_risk:
            return False

        if stop_loss is not None:
            if not (self.sl_range[0] <= stop_loss <= self.sl_range[1]):
                return False
        if take_profit is not None:
            if not (self.tp_range[0] <= take_profit <= self.tp_range[1]):
                return False

        return True

    def register_trade_result(self, pnl: float) -> None:
        """Update daily PnL and trade count after a trade closes."""
        self._reset_if_new_day()
        self.current_day_pnl += pnl
        self.trade_count_today += 1
        self.capital += pnl

    def check_daily_limit(self) -> bool:
        """Return True if daily loss limit has been breached."""
        max_loss_amount = self.capital * self.max_daily_loss
        return self.current_day_pnl <= -max_loss_amount
