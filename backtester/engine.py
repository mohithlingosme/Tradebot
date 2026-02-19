from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Union

from common.market_data import Candle
from trading_engine.phase4.models import (
    Bar,
    OrderFill,
    OrderRequest,
    OrderSide,
    OrderType,
    PortfolioState,
    RiskDecisionType,
    Signal,
    SignalAction,
    Tick,
)
from trading_engine.phase4.position_sizing import PositionSizer
from trading_engine.phase4.risk import RiskManager
from trading_engine.phase4.strategy import Strategy

from risk.risk_engine import RiskEngine
from .config import BacktestConfig
from .costs import CostModel
from .reporting import BacktestReport, build_performance_report, plot_equity_curve
from .risk_manager import BacktestRiskManager, RiskLimits
from .simulator import TradeSimulator

MarketEvent = Union[Bar, Tick]


@dataclass
class TradeRecord:
    """Simple representation of a completed trade."""

    symbol: str
    side: str
    quantity: float
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    pnl: float


@dataclass
class EquityPoint:
    timestamp: datetime
    equity: float


@dataclass
class BacktestMetrics:
    total_pnl: float
    win_rate: float
    max_drawdown: float
    profit_factor: float


@dataclass
class SimpleBacktestResult:
    trades: List[TradeRecord]
    equity_curve: List[EquityPoint]
    metrics: BacktestMetrics


def _default_fill_price(bar: Candle | Bar, side: str, execution_model) -> float:
    if execution_model:
        filler = getattr(execution_model, "fill_price", None)
        if callable(filler):
            return float(filler(bar, side))
    return float(getattr(bar, "close", bar.price if hasattr(bar, "price") else 0.0))


def _risk_allows(symbol: str, side: str, quantity: float, price: float, risk_engine) -> bool:
    if not risk_engine:
        return True
    approve = getattr(risk_engine, "approve_trade", None)
    if callable(approve):
        return bool(approve(symbol=symbol, side=side, quantity=quantity, price=price))
    return True


def _mark_to_market(cash: float, positions: Dict[str, Dict[str, float]], last_prices: Dict[str, float]) -> float:
    equity = cash
    for symbol, position in positions.items():
        equity += position["qty"] * last_prices.get(symbol, position["entry_price"])
    return equity


def _max_drawdown(equity_curve: List[EquityPoint]) -> float:
    peak = equity_curve[0].equity if equity_curve else 0.0
    max_dd = 0.0
    for point in equity_curve:
        if point.equity > peak:
            peak = point.equity
        drawdown = (peak - point.equity) / peak if peak else 0.0
        max_dd = max(max_dd, drawdown)
    return max_dd


def _profit_factor(trades: List[TradeRecord]) -> float:
    gains = sum(trade.pnl for trade in trades if trade.pnl > 0)
    losses = sum(-trade.pnl for trade in trades if trade.pnl < 0)
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def run_backtest(strategy: Strategy, data: Sequence[Candle], initial_capital: float, risk_engine: RiskEngine | None = None, execution_model=None) -> SimpleBacktestResult:
    """
    Simple single-strategy backtest loop.

    Args:
        strategy: Strategy instance implementing `on_bar`.
        data: Iterable of normalized candles sorted by timestamp.
        initial_capital: Starting equity for the simulation.
        risk_engine: Optional object with `approve_trade(**kwargs) -> bool`.
        execution_model: Optional object with `fill_price(bar, side) -> float`.

    Returns:
        SimpleBacktestResult containing trades, equity curve, and summary metrics.
    """
    cash = initial_capital
    positions: Dict[str, Dict[str, float]] = {}
    trades: List[TradeRecord] = []
    equity_curve: List[EquityPoint] = []
    last_prices: Dict[str, float] = {}

    engine = risk_engine or RiskEngine(capital=initial_capital)

    for bar in data:
        last_prices[bar.symbol] = bar.close
        signal = strategy.on_bar(bar, strategy.state)
        quantity = 1.0  # simple V1 sizing

        if signal == "BUY" and bar.symbol not in positions:
            fill_price = _default_fill_price(bar, "BUY", execution_model)
            stop_distance = getattr(strategy.state, "stop_distance", abs(getattr(bar, "close", fill_price) * 0.01))
            if not engine.can_open_trade(quantity, stop_distance):
                continue
            positions[bar.symbol] = {
                "qty": quantity,
                "entry_price": fill_price,
                "entry_time": bar.timestamp,
            }
            cash -= quantity * fill_price
        elif signal == "SELL" and bar.symbol in positions:
            fill_price = _default_fill_price(bar, "SELL", execution_model)
            position = positions.pop(bar.symbol)
            cash += position["qty"] * fill_price
            pnl = (fill_price - position["entry_price"]) * position["qty"]
            trades.append(
                TradeRecord(
                    symbol=bar.symbol,
                    side="LONG",
                    quantity=position["qty"],
                    entry_time=position["entry_time"],
                    exit_time=bar.timestamp,
                    entry_price=position["entry_price"],
                    exit_price=fill_price,
                    pnl=pnl,
                )
            )
            engine.register_trade_result(pnl)

        equity_curve.append(
            EquityPoint(timestamp=bar.timestamp, equity=_mark_to_market(cash, positions, last_prices))
        )

    # Close any residual positions at last known prices
    for symbol, position in list(positions.items()):
        last_price = last_prices.get(symbol, position["entry_price"])
        cash += position["qty"] * last_price
        pnl = (last_price - position["entry_price"]) * position["qty"]
        trades.append(
            TradeRecord(
                symbol=symbol,
                side="LONG",
                quantity=position["qty"],
                entry_time=position["entry_time"],
                exit_time=datetime.utcnow(),
                entry_price=position["entry_price"],
                exit_price=last_price,
                pnl=pnl,
            )
        )
        positions.pop(symbol)

    total_pnl = cash - initial_capital
    wins = len([trade for trade in trades if trade.pnl > 0])
    win_rate = wins / len(trades) if trades else 0.0
    metrics = BacktestMetrics(
        total_pnl=total_pnl,
        win_rate=win_rate,
        max_drawdown=_max_drawdown(equity_curve) if equity_curve else 0.0,
        profit_factor=_profit_factor(trades),
    )

    _persist_backtest_artifacts(trades, metrics)
    # TODO: integrate slippage, latency, commission/tax models, and walk-forward validation.
    return SimpleBacktestResult(trades=trades, equity_curve=equity_curve, metrics=metrics)


def _persist_backtest_artifacts(trades: List[TradeRecord], metrics: BacktestMetrics) -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    trades_path = logs_dir / "backtest_trades.csv"
    with trades_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "symbol",
                "side",
                "quantity",
                "entry_time",
                "exit_time",
                "entry_price",
                "exit_price",
                "pnl",
            ],
        )
        writer.writeheader()
        for trade in trades:
            row = asdict(trade)
            row["entry_time"] = trade.entry_time.isoformat()
            row["exit_time"] = trade.exit_time.isoformat()
            writer.writerow(row)

    summary_path = logs_dir / "backtest_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "metrics": asdict(metrics),
                "trade_count": len(trades),
            },
            f,
            indent=2,
            default=str,
        )


class EventBacktester:
    """Event-driven backtester supporting bars and ticks."""

    def __init__(
        self,
        config: BacktestConfig,
        strategies: Sequence[Strategy],
        cost_model: CostModel | None = None,
        risk_manager: BacktestRiskManager | None = None,
        position_sizer: PositionSizer | None = None,
    ):
        self.config = config
        self.strategies: Dict[str, Strategy] = {s.name: s for s in strategies}
        self.cost_model = cost_model or CostModel(
            slippage_bps=config.slippage_bps,
            commission_rate=config.commission_rate,
            fee_per_order=config.fee_per_order,
            fee_per_unit=config.fee_per_unit,
        )
        self.position_sizer = position_sizer or config.position_sizer or PositionSizer()
        # Use BacktestRiskManager with default RiskLimits if not provided
        if risk_manager is None:
            limits = RiskLimits()  # Default limits
            self.risk_manager = BacktestRiskManager(limits)
        else:
            self.risk_manager = risk_manager

        portfolio = PortfolioState(cash=config.initial_capital, daily_start_equity=config.initial_capital)
        self.simulator = TradeSimulator(self.cost_model, portfolio=portfolio)

        self.trades: List[OrderFill] = []
        self.equity_curve: List[tuple] = [(self.config.start, self.simulator.portfolio.equity)]

    def run(
        self,
        events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]],
        plot_path: str | None = None,
    ) -> BacktestReport:
        normalized_events = self._normalize_events(events)
        for event in normalized_events:
            if event.timestamp < self.config.start or event.timestamp > self.config.end:
                continue
            if isinstance(event, Bar):
                fills = self._on_bar(event)
            else:
                fills = self._on_tick(event)
            if fills:
                self.trades.extend(fills)
            self.equity_curve.append((event.timestamp, self.simulator.portfolio.equity))

        performance = build_performance_report(
            equity_curve=self.equity_curve,
            trades=self.trades,
            start=self.config.start,
            end=self.config.end,
            fees_paid=self.simulator.fees_paid,
            risk_free_rate=self.config.risk_free_rate,
        )

        if plot_path:
            plot_equity_curve(self.equity_curve, plot_path)

        return BacktestReport(
            performance=performance,
            trades=self.trades,
            equity_curve=self.equity_curve,
            plot_path=plot_path,
        )

    def _on_bar(self, bar: Bar) -> List[OrderFill]:
        fills = self.simulator.mark_to_market(bar)
        for strategy in self.strategies.values():
            signals = strategy.on_bar(bar) or []
            fills.extend(self._process_signals(strategy.name, signals, price=bar.close, execution_bar=bar))
        return fills

    def _on_tick(self, tick: Tick) -> List[OrderFill]:
        synthetic_bar = self._synthetic_bar(tick)
        fills = self.simulator.mark_to_market(synthetic_bar)
        for strategy in self.strategies.values():
            signals = strategy.on_tick(tick) or []
            fills.extend(self._process_signals(strategy.name, signals, price=tick.price, execution_bar=synthetic_bar))
        return fills

    def _process_signals(
        self, strategy_name: str, signals: Sequence[Signal], price: float, execution_bar: Bar
    ) -> List[OrderFill]:
        fills: List[OrderFill] = []
        rejected_signals = []  # Track rejected signals for reporting

        for signal in signals:
            order = self._signal_to_order(signal, price, strategy_name)
            if order is None:
                continue

            # Get ATR from strategy indicators for position sizing
            atr = None
            if hasattr(self.strategies[strategy_name], 'get_indicator'):
                try:
                    atr = self.strategies[strategy_name].get_indicator(signal.symbol, 'atr_14', [])
                except:
                    pass  # ATR not available, use default sizing

            # Evaluate order with risk manager (now includes position sizing)
            backtest_order = self._order_request_to_backtest_order(order, price)
            decision = self.risk_manager.evaluate_order(
                backtest_order, self.simulator.portfolio, execution_bar.timestamp, Decimal(str(price)), atr
            )

            if decision.action == RiskDecisionType.REJECT:
                rejected_signals.append({
                    'signal': signal,
                    'reason': decision.reason,
                    'timestamp': execution_bar.timestamp
                })
                continue
            elif decision.action == RiskDecisionType.HALT_TRADING:
                # Trading halted, stop processing signals for this bar
                break

            # Execute the approved order
            final_order = decision.order
            fill = self.simulator.execute(final_order, execution_bar)
            fills.append(fill)

        # Store rejected signals for reporting (could be added to BacktestReport)
        if rejected_signals:
            # For now, just log them; in full implementation, add to report
            pass

        return fills

    def _signal_to_order(self, signal: Signal, price: float, strategy_name: str) -> OrderRequest | None:
        stop_loss = signal.metadata.get("stop_loss") if signal.metadata else None
        take_profit = signal.metadata.get("take_profit") if signal.metadata else None
        trailing_stop = signal.metadata.get("trailing_stop") if signal.metadata else None

        if signal.action == SignalAction.FLAT:
            position = self.simulator.portfolio.positions.get(signal.symbol)
            quantity = position.quantity if position else 0.0
            if quantity <= 0:
                return None
            side = OrderSide.SELL
        else:
            quantity = self.position_sizer.size_order(signal, price, self.simulator.portfolio, stop_loss)
            side = OrderSide.BUY if signal.action == SignalAction.BUY else OrderSide.SELL
            if quantity <= 0:
                return None

        return OrderRequest(
            symbol=signal.symbol,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET,
            limit_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=trailing_stop,
            strategy_name=strategy_name,
            metadata=signal.metadata or {},
        )

    @staticmethod
    def _synthetic_bar(tick: Tick) -> Bar:
        return Bar(
            symbol=tick.symbol,
            timestamp=tick.timestamp,
            open=tick.price,
            high=tick.price,
            low=tick.price,
            close=tick.price,
            volume=tick.size,
        )

    def _order_request_to_backtest_order(self, order: OrderRequest, price: float):
        """Convert OrderRequest to BacktestOrder for risk evaluation."""
        from .fill_simulator import BacktestOrder, OrderSide as BOOrderSide, OrderType as BOOrderType
        side = BOOrderSide.BUY if order.side == OrderSide.BUY else BOOrderSide.SELL
        order_type = BOOrderType.MARKET if order.order_type == OrderType.MARKET else BOOrderType.LIMIT
        return BacktestOrder(
            order_id=f"{order.strategy_name}_{order.symbol}_{order.timestamp.isoformat()}" if hasattr(order, 'timestamp') else f"{order.strategy_name}_{order.symbol}",
            symbol=order.symbol,
            side=side,
            order_type=order_type,
            quantity=order.quantity,
            price=price if order_type == BOOrderType.LIMIT else None,
        )

    @staticmethod
    def _normalize_events(events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]]) -> List[MarketEvent]:
        if isinstance(events, dict):
            flattened: List[MarketEvent] = []
            for series in events.values():
                flattened.extend(series)
            events = flattened
        return sorted(list(events), key=lambda e: e.timestamp)
