from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Union

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

from .config import BacktestConfig
from .costs import CostModel
from .reporting import BacktestReport, build_performance_report
from .simulator import TradeSimulator

MarketEvent = Union[Bar, Tick]


class EventBacktester:
    """Event-driven backtester supporting bars and ticks."""

    def __init__(
        self,
        config: BacktestConfig,
        strategies: Sequence[Strategy],
        cost_model: CostModel | None = None,
        risk_manager: RiskManager | None = None,
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
        self.risk_manager = risk_manager or RiskManager(config.risk_limits)

        portfolio = PortfolioState(cash=config.initial_capital, daily_start_equity=config.initial_capital)
        self.simulator = TradeSimulator(self.cost_model, portfolio=portfolio)

        self.trades: List[OrderFill] = []
        self.equity_curve: List[tuple] = [(self.config.start, self.simulator.portfolio.equity)]

    def run(self, events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]]) -> BacktestReport:
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
        return BacktestReport(performance=performance, trades=self.trades, equity_curve=self.equity_curve)

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
        for signal in signals:
            order = self._signal_to_order(signal, price, strategy_name)
            if order is None:
                continue
            decision = self.risk_manager.evaluate(order, self.simulator.portfolio, order.limit_price or price)
            if decision.decision == RiskDecisionType.REJECT or decision.order is None:
                continue
            final_order = decision.order
            fill = self.simulator.execute(final_order, execution_bar)
            fills.append(fill)
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

    @staticmethod
    def _normalize_events(events: Union[Dict[str, Sequence[MarketEvent]], Iterable[MarketEvent]]) -> List[MarketEvent]:
        if isinstance(events, dict):
            flattened: List[MarketEvent] = []
            for series in events.values():
                flattened.extend(series)
            events = flattened
        return sorted(list(events), key=lambda e: e.timestamp)
