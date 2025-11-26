"""
Reporting helpers for backtests.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from .models import OrderFill

if TYPE_CHECKING:  # pragma: no cover
    from .backtest import BacktestReport


def export_report(report: "BacktestReport", directory: str) -> None:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)

    trades_path = path / "trades.csv"
    with trades_path.open("w", encoding="utf-8") as f:
        f.write("timestamp,symbol,side,quantity,price,pnl,status,reason\n")
        for fill in report.trades:
            fill_dict = _fill_to_row(fill)
            f.write(",".join(fill_dict) + "\n")

    equity_path = path / "equity_curve.csv"
    with equity_path.open("w", encoding="utf-8") as f:
        f.write("timestamp,equity\n")
        for ts, value in report.equity_curve:
            f.write(f"{ts.isoformat()},{value}\n")

    metrics_path = path / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(asdict(report.metrics), f, indent=2)


def _fill_to_row(fill: OrderFill) -> list[str]:
    return [
        fill.timestamp.isoformat(),
        fill.order.symbol,
        fill.order.side.value,
        f"{fill.filled_quantity}",
        f"{fill.fill_price}",
        f"{fill.pnl}",
        fill.status.value,
        fill.reason or "",
    ]
