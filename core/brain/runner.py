from __future__ import annotations

"""Simple backtesting runner for Finbot strategies."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Type

import pandas as pd
from zoneinfo import ZoneInfo

from data_engine.candle import Candle

from ..signals import Signal
from ..strategies import Strategy

TZ = ZoneInfo("Asia/Kolkata")


@dataclass
class TradeRecord:
    side: str
    entry_ts: datetime
    exit_ts: datetime
    entry_price: float
    exit_price: float
    qty: float
    pnl: float


@dataclass
class BacktestMetrics:
    sharpe: Optional[float]
    max_drawdown: float
    win_rate: Optional[float]
    profit_factor: Optional[float]
    total_pnl: float
    trades: int


@dataclass
class BacktestResult:
    metrics: BacktestMetrics
    trades: List[TradeRecord]
    equity_curve: List[Tuple[datetime, float]]


def load_candles_from_csv(
    csv_path: Path,
    symbol: str,
    timeframe_s: int,
) -> List[Candle]:
    df = pd.read_csv(csv_path)
    if "timestamp" not in df.columns or "price" not in df.columns:
        raise ValueError("CSV must contain timestamp and price columns")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=False)
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize(TZ)
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert(TZ)
    df = df.set_index("timestamp").sort_index()
    rule = f"{timeframe_s}s"
    ohlc = df["price"].resample(rule, label="left", closed="left").ohlc()
    ohlc.columns = ["open", "high", "low", "close"]
    volume = df.get("volume", pd.Series(0, index=df.index))
    volume = volume.resample(rule, label="left", closed="left").sum().fillna(0.0)
    merged = ohlc.join(volume.rename("volume"), how="inner").dropna()
    candles: List[Candle] = []
    for idx, row in merged.iterrows():
        start_ts = idx.to_pydatetime()
        end_ts = start_ts + timedelta(seconds=timeframe_s)
        candles.append(
            Candle(
                symbol=symbol,
                timeframe_s=timeframe_s,
                start_ts=start_ts,
                end_ts=end_ts,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
                vwap=None,
            )
        )
    return candles


def run_backtest(
    strategy_cls: Type[Strategy],
    strategy_config,
    candles: Sequence[Candle],
    initial_cash: float = 100_000.0,
) -> BacktestResult:
    strategy = strategy_cls(data_feed=None, symbol=strategy_config.symbol, config=strategy_config)
    cash = initial_cash
    position: Optional[Dict] = None
    trades: List[TradeRecord] = []
    equity_curve: List[Tuple[datetime, float]] = []

    def mark_to_market(last_price: float) -> float:
        eq = cash
        if position:
            qty = position["qty"]
            if position["side"] == "LONG":
                eq += last_price * qty
            else:
                eq += position["entry_price"] * qty - last_price * qty
        return eq

    for candle in candles:
        signals = strategy.on_candle(candle)
        for signal in signals:
            cash, position, trade = _apply_signal(signal, cash, position, candle)
            if trade:
                trades.append(trade)
        equity_curve.append((candle.end_ts, mark_to_market(candle.close)))

    if position:
        forced_signal = Signal(
            action="CLOSE",
            symbol=strategy_config.symbol,
            price=None,
            order_type="MARKET",
            ts=candles[-1].end_ts,
            meta={"reason": "session_end"},
        )
        cash, position, trade = _apply_signal(forced_signal, cash, position, candles[-1])
        if trade:
            trades.append(trade)
        equity_curve.append((candles[-1].end_ts, cash))

    metrics = _compute_metrics(trades, equity_curve)
    return BacktestResult(metrics=metrics, trades=trades, equity_curve=equity_curve)


def _apply_signal(
    signal: Signal,
    cash: float,
    position: Optional[Dict],
    candle: Candle,
) -> Tuple[float, Optional[Dict], Optional[TradeRecord]]:
    fill_price = signal.price if signal.price is not None else candle.close
    qty = signal.qty or 1.0
    trade: Optional[TradeRecord] = None
    if signal.action == "BUY" and position is None:
        cash -= fill_price * qty
        position = {"side": "LONG", "entry_price": fill_price, "qty": qty, "entry_ts": signal.ts}
    elif signal.action == "SELL" and position is None:
        cash += fill_price * qty
        position = {"side": "SHORT", "entry_price": fill_price, "qty": qty, "entry_ts": signal.ts}
    elif signal.action == "CLOSE" and position:
        qty = position["qty"]
        if position["side"] == "LONG":
            cash += fill_price * qty
            pnl = (fill_price - position["entry_price"]) * qty
        else:
            cash -= fill_price * qty
            pnl = (position["entry_price"] - fill_price) * qty
        trade = TradeRecord(
            side=position["side"],
            entry_ts=position["entry_ts"],
            exit_ts=signal.ts,
            entry_price=position["entry_price"],
            exit_price=fill_price,
            qty=qty,
            pnl=pnl,
        )
        position = None
    return cash, position, trade


def _compute_metrics(trades: Sequence[TradeRecord], equity_curve: Sequence[Tuple[datetime, float]]) -> BacktestMetrics:
    total_pnl = sum(trade.pnl for trade in trades)
    wins = [trade for trade in trades if trade.pnl > 0]
    losses = [trade for trade in trades if trade.pnl < 0]
    win_rate = len(wins) / len(trades) if trades else None
    profit_factor: Optional[float]
    loss_sum = abs(sum(trade.pnl for trade in losses))
    if loss_sum == 0:
        profit_factor = float("inf") if wins else None
    else:
        profit_factor = sum(trade.pnl for trade in wins) / loss_sum

    returns = [
        trade.pnl / (abs(trade.entry_price) * trade.qty) for trade in trades if trade.entry_price != 0
    ]
    sharpe: Optional[float] = None
    if len(returns) > 1:
        sharpe = mean(returns) / (pstdev(returns) or 1e-9)
        sharpe *= len(returns) ** 0.5

    max_dd = _max_drawdown(equity_curve)
    return BacktestMetrics(
        sharpe=sharpe,
        max_drawdown=max_dd,
        win_rate=win_rate,
        profit_factor=profit_factor,
        total_pnl=total_pnl,
        trades=len(trades),
    )


def _max_drawdown(equity_curve: Sequence[Tuple[datetime, float]]) -> float:
    peak = float("-inf")
    max_dd = 0.0
    for _, value in equity_curve:
        if value > peak:
            peak = value
        if peak <= 0:
            continue
        drawdown = (peak - value) / peak
        max_dd = max(max_dd, drawdown)
    return max_dd


def save_report(result: BacktestResult, path: Path) -> None:
    data = {
        "metrics": result.metrics.__dict__,
        "trades": [trade.__dict__ for trade in result.trades],
        "equity_curve": [(ts.isoformat(), value) for ts, value in result.equity_curve],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
