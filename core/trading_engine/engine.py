"""
Core trading engine that wires strategies to risk, circuit breakers, and paper execution.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from .circuit_breaker import GlobalCircuitBreaker, StrategyCircuitBreaker
from .models import (
    Bar,
    OrderFill,
    OrderRequest,
    OrderSide,
    OrderType,
    RiskDecisionType,
    Signal,
    SignalAction,
)
from .paper_engine import PaperTradingEngine
from .position_sizing import PositionSizer
from .risk import RiskManager
from .strategy import Strategy

try:
    from backend.monitoring.logger import StructuredLogger, LogLevel, Component
except Exception:  # pragma: no cover - optional dependency
    StructuredLogger = None  # type: ignore
    LogLevel = None  # type: ignore
    Component = None  # type: ignore


class TradingEngine:
    """Routes market data through strategies → risk → circuit breakers → paper execution."""

    def __init__(
        self,
        strategies: List[Strategy],
        risk_manager: RiskManager,
        paper_engine: Optional[PaperTradingEngine] = None,
        position_sizer: Optional[PositionSizer] = None,
        global_circuit_breaker: Optional[GlobalCircuitBreaker] = None,
        strategy_breakers: Optional[Dict[str, StrategyCircuitBreaker]] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        self.strategies: Dict[str, Strategy] = {s.name: s for s in strategies}
        self.risk_manager = risk_manager
        self.paper_engine = paper_engine or PaperTradingEngine()
        self.position_sizer = position_sizer or PositionSizer()
        self.global_circuit_breaker = global_circuit_breaker
        self.strategy_breakers = strategy_breakers or {}
        self.logger = logger
        self.equity_curve: List[tuple[datetime, float]] = []

    def on_bar(self, bar: Bar) -> List[OrderFill]:
        fills: List[OrderFill] = []
        fills.extend(self.paper_engine.update_mark_to_market(bar))

        for strategy_name, strategy in self.strategies.items():
            if not self._strategy_can_trade(strategy_name):
                continue

            signals = strategy.on_bar(bar) or []
            for signal in signals:
                if not self._global_can_trade():
                    continue

                order = self._signal_to_order(strategy_name, signal, bar)
                if order is None or order.quantity <= 0:
                    continue
                decision = self.risk_manager.evaluate(order, self.paper_engine.portfolio, order.limit_price or bar.close)
                if decision.decision == RiskDecisionType.REJECT or decision.order is None:
                    continue

                final_order = decision.order
                fill = self.paper_engine.execute_order(final_order, bar)
                fills.append(fill)
                self._update_breakers(strategy_name, fill)

        self.equity_curve.append((bar.timestamp, self.paper_engine.portfolio.equity))
        return fills

    def _signal_to_order(self, strategy_name: str, signal: Signal, bar: Bar) -> Optional[OrderRequest]:
        price = bar.close
        stop_loss = signal.metadata.get("stop_loss") if signal.metadata else None
        take_profit = signal.metadata.get("take_profit") if signal.metadata else None
        trailing_stop = signal.metadata.get("trailing_stop") if signal.metadata else None

        if signal.action == SignalAction.FLAT:
            position = self.paper_engine.portfolio.positions.get(signal.symbol)
            quantity = position.quantity if position else 0.0
            if quantity <= 0:
                return None
            side = OrderSide.SELL
        else:
            quantity = self.position_sizer.size_order(signal, price, self.paper_engine.portfolio, stop_loss)
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

    def _update_breakers(self, strategy_name: str, fill: OrderFill) -> None:
        strategy_breaker = self.strategy_breakers.get(strategy_name)
        if strategy_breaker:
            strategy_breaker.record_trade(fill.pnl, self.paper_engine.portfolio.equity)

        if self.global_circuit_breaker:
            self.global_circuit_breaker.observe(self.paper_engine.portfolio.equity)

    def _global_can_trade(self) -> bool:
        if self.global_circuit_breaker and not self.global_circuit_breaker.can_trade():
            self._log(LogLevel.WARNING if LogLevel else None, "Global circuit breaker triggered")
            return False
        return True

    def _strategy_can_trade(self, strategy_name: str) -> bool:
        breaker = self.strategy_breakers.get(strategy_name)
        if breaker and not breaker.can_trade():
            self._log(LogLevel.WARNING if LogLevel else None, f"Strategy {strategy_name} paused by circuit breaker")
            return False
        return True

    def _log(self, level, message: str) -> None:
        if self.logger and level and Component:
            self.logger.log(level, Component.STRATEGY, message)
