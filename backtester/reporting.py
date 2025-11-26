from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from statistics import mean, pstdev
from typing import Dict, List, Tuple

from trading_engine.phase4.models import OrderFill


@dataclass
class PerformanceReport:
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    trade_count: int = 0
    fees_paid: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "trade_count": self.trade_count,
            "fees_paid": self.fees_paid,
        }


@dataclass
class BacktestReport:
    performance: PerformanceReport
    trades: List[OrderFill]
    equity_curve: List[Tuple[datetime, float]]

    def to_dict(self) -> Dict:
        return {
            "performance": self.performance.to_dict(),
            "trades": [
                {
                    "symbol": t.order.symbol,
                    "side": t.order.side.value,
                    "quantity": t.filled_quantity,
                    "price": t.fill_price,
                    "timestamp": t.timestamp.isoformat(),
                    "pnl": t.pnl,
                    "status": t.status.value,
                    "reason": t.reason,
                }
                for t in self.trades
            ],
            "equity_curve": [{"timestamp": ts.isoformat(), "equity": eq} for ts, eq in self.equity_curve],
        }


def build_performance_report(
    equity_curve: List[Tuple[datetime, float]],
    trades: List[OrderFill],
    start: datetime,
    end: datetime,
    fees_paid: float,
    risk_free_rate: float = 0.0,
) -> PerformanceReport:
    report = PerformanceReport(fees_paid=fees_paid, trade_count=len(trades))
    if not equity_curve:
        return report

    initial = equity_curve[0][1]
    final = equity_curve[-1][1]
    report.total_return = (final - initial) / initial if initial else 0.0

    days = max((end - start).days, 1)
    report.annualized_return = (1 + report.total_return) ** (365 / days) - 1 if days > 0 else report.total_return

    returns = []
    for (_, prev), (_, curr) in zip(equity_curve[:-1], equity_curve[1:]):
        if prev > 0:
            returns.append((curr - prev) / prev)

    if len(returns) > 1:
        std = pstdev(returns)
        report.volatility = std * sqrt(252)
        if std > 0:
            excess = mean(returns) - (risk_free_rate / 252)
            report.sharpe_ratio = (excess / std) * sqrt(252)

    report.max_drawdown = _max_drawdown(equity_curve)

    if trades:
        wins = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl < 0]
        if wins:
            report.avg_win = sum(wins) / len(wins)
        if losses:
            report.avg_loss = abs(sum(losses) / len(losses))
        total_wins = sum(wins)
        total_losses = abs(sum(losses))
        if total_losses > 0:
            report.profit_factor = total_wins / total_losses
        report.win_rate = len(wins) / len(trades)
    return report


def _max_drawdown(equity_curve: List[Tuple[datetime, float]]) -> float:
    peak = equity_curve[0][1]
    max_dd = 0.0
    for _, value in equity_curve:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak if peak else 0.0
        if drawdown > max_dd:
            max_dd = drawdown
    return max_dd
