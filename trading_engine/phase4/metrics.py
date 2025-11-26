"""
Performance metrics utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from statistics import mean, pstdev
from typing import List, Tuple

from .models import OrderFill


@dataclass
class PerformanceMetrics:
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    drawdown_duration: int = 0
    trades: int = 0


def calculate_performance(equity_curve: List[Tuple[datetime, float]], trades: List[OrderFill]) -> PerformanceMetrics:
    metrics = PerformanceMetrics()
    if not equity_curve:
        return metrics

    start_equity = equity_curve[0][1]
    end_equity = equity_curve[-1][1]
    metrics.total_return = (end_equity - start_equity) / start_equity if start_equity else 0.0
    metrics.sharpe_ratio = _sharpe_ratio(equity_curve)
    metrics.max_drawdown, metrics.drawdown_duration = _max_drawdown(equity_curve)

    if trades:
        wins = [t for t in trades if t.pnl > 0]
        metrics.win_rate = len(wins) / len(trades)
        metrics.trades = len(trades)
    return metrics


def _sharpe_ratio(equity_curve: List[Tuple[datetime, float]]) -> float:
    if len(equity_curve) < 2:
        return 0.0
    returns = []
    for (_, prev_equity), (_, curr_equity) in zip(equity_curve[:-1], equity_curve[1:]):
        if prev_equity > 0:
            returns.append((curr_equity - prev_equity) / prev_equity)
    if not returns:
        return 0.0
    std = pstdev(returns)
    if std == 0:
        return 0.0
    return (mean(returns) / std) * sqrt(252)


def _max_drawdown(equity_curve: List[Tuple[datetime, float]]) -> tuple[float, int]:
    peak = equity_curve[0][1]
    max_dd = 0.0
    duration = 0
    temp_duration = 0

    for _, equity in equity_curve:
        if equity > peak:
            peak = equity
            temp_duration = 0
        else:
            drawdown = (peak - equity) / peak if peak else 0.0
            temp_duration += 1
            if drawdown > max_dd:
                max_dd = drawdown
                duration = temp_duration
    return max_dd, duration
