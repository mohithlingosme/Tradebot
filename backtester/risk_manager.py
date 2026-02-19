"""
Risk management for backtesting with parity to live/paper trading.

Implements position sizing, risk limits, circuit breakers, and trade cooldowns.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .account import BacktestAccount
from .fill_simulator import BacktestOrder, OrderSide


class RiskDecisionType(Enum):
    ALLOW = "allow"
    REJECT = "reject"
    MODIFY = "modify"
    HALT_TRADING = "halt_trading"


@dataclass
class RiskDecision:
    action: RiskDecisionType
    order: Optional[BacktestOrder] = None
    reason: str = ""


@dataclass
class RiskLimits:
    """Configurable risk limits for backtesting."""

    # Position sizing
    default_sizing_method: str = "fixed"  # "fixed_qty", "percent_equity", "atr_volatility"
    fixed_quantity: int = 1
    percent_equity_per_trade: float = 1.0  # % of equity per trade
    atr_multiplier: float = 2.0  # For ATR-based sizing

    # Enforcement limits
    max_positions: int = 10
    per_symbol_limits: Dict[str, int] = field(default_factory=dict)  # Max positions per symbol
    exposure_caps: Dict[str, float] = field(default_factory=dict)  # Max exposure % per symbol

    # Circuit Breakers
    daily_loss_limit: float = 5.0  # % daily loss that triggers circuit breaker
    max_drawdown_stop: float = 10.0  # % drawdown that triggers circuit breaker

    # Cooldowns
    trade_cooldown_minutes: int = 60  # Minutes to wait after stop-out before re-entry

    # Legacy fields for backward compatibility
    max_exposure_pct: float = 50.0  # Max % of equity in positions
    per_symbol_limit_pct: float = 10.0  # Max % per symbol
    max_daily_loss_pct: float = 5.0
    max_drawdown_stop_pct: float = 10.0
    circuit_breaker_threshold_pct: float = 15.0
    cooldown_period_minutes: int = 60


class PositionSizer:
    """Handles position sizing calculations."""

    def __init__(self, limits: RiskLimits):
        self.limits = limits

    def calculate_position_size(self, symbol: str, price: Decimal, account: BacktestAccount,
                               atr: Optional[float] = None) -> int:
        """Calculate position size based on sizing method."""
        if self.limits.default_sizing_method == "fixed":
            return self.limits.fixed_quantity
        elif self.limits.default_sizing_method == "percent_equity":
            equity = account.equity
            risk_amount = equity * Decimal(str(self.limits.percent_equity_per_trade / 100))
            return int(risk_amount / price)
        elif self.limits.default_sizing_method == "atr_volatility" and atr:
            # ATR-based sizing: risk 1 ATR per trade
            risk_amount = account.equity * Decimal(str(self.limits.percent_equity_per_trade / 100))
            position_size = risk_amount / (price * Decimal(str(atr * self.limits.atr_multiplier)))
            return max(1, int(position_size))
        else:
            return self.limits.fixed_quantity


class BacktestRiskManager:
    """Risk manager for backtesting with comprehensive checks."""

    def __init__(self, limits: RiskLimits):
        self.limits = limits
        self.position_sizer = PositionSizer(limits)
        self.daily_pnl = Decimal('0')
        self.peak_equity = Decimal('0')
        self.current_drawdown_pct = 0.0
        self.circuit_breaker_triggered = False
        self.trading_disabled = False  # Session-level trading disable
        self.last_trade_time: Optional[datetime] = None
        self.symbol_exposure: Dict[str, Decimal] = {}
        self.trade_log: List[Tuple[datetime, str, Decimal]] = []  # (time, symbol, pnl)

        # Daily tracking state
        self.current_day: Optional[date] = None
        self.daily_pnl_by_day: Dict[date, Decimal] = {}
        self.cooldown_until: Optional[datetime] = None

    def evaluate_order(self, order: BacktestOrder, account: BacktestAccount,
                      timestamp: datetime, price: Decimal, atr: Optional[float] = None) -> RiskDecision:
        """Evaluate order against all risk limits."""

        # Reset daily state if new day
        self._reset_if_new_day(timestamp.date())

        # Check session-level circuit breaker
        if self.trading_disabled:
            return RiskDecision(RiskDecisionType.HALT_TRADING, reason="Trading disabled for session")

        # Check circuit breaker
        if self.circuit_breaker_triggered:
            return RiskDecision(RiskDecisionType.HALT_TRADING, reason="Circuit breaker active")

        # Check trade cooldowns
        if self._check_trade_cooldowns(timestamp):
            return RiskDecision(RiskDecisionType.REJECT, reason="Trade cooldown active")

        # Check daily loss limit
        if not self._check_daily_loss_limit(account, timestamp.date()):
            self.trading_disabled = True
            return RiskDecision(RiskDecisionType.HALT_TRADING, reason="Daily loss limit reached")

        # Check max drawdown stop
        if self.current_drawdown_pct >= self.limits.max_drawdown_stop:
            self.circuit_breaker_triggered = True
            return RiskDecision(RiskDecisionType.HALT_TRADING, reason="Max drawdown stop triggered")

        # Check position limits
        if not self._check_position_limits(order, account, price):
            return RiskDecision(RiskDecisionType.REJECT, reason="Position limits exceeded")

        # Check exposure limits
        if not self._check_exposure_limits(order, account, price):
            return RiskDecision(RiskDecisionType.REJECT, reason="Exposure limits exceeded")

        # All checks passed - apply position sizing
        sized_order = self._apply_position_sizing(order, account, price, atr)
        return RiskDecision(RiskDecisionType.ALLOW, sized_order)

    def _check_daily_limit(self, account: BacktestAccount) -> bool:
        """Check if daily loss limit has been breached."""
        # In backtesting, we track pnl across the session
        # For simplicity, assume daily reset at start, but in practice, track per day
        max_loss = account.starting_cash * Decimal(str(self.limits.max_daily_loss_pct / 100))
        return abs(self.daily_pnl) <= max_loss

    def _check_position_limits(self, order: BacktestOrder, account: BacktestAccount, price: Decimal) -> bool:
        """Check max positions and per-symbol limits."""
        current_positions = len([p for p in account.positions.values() if p.quantity != 0])

        if order.side == OrderSide.BUY:
            new_positions = current_positions + 1
        else:
            # For sell, check if closing existing
            if order.symbol not in account.positions or account.positions[order.symbol].quantity == 0:
                return True  # Allow short or something, but for simplicity
            new_positions = current_positions

        if new_positions > self.limits.max_positions:
            return False

        # Per-symbol check
        current_symbol_value = self.symbol_exposure.get(order.symbol, Decimal('0'))
        order_value = abs(order.quantity) * price
        if order.side == OrderSide.BUY:
            new_symbol_value = current_symbol_value + order_value
        else:
            new_symbol_value = max(0, current_symbol_value - order_value)

        max_symbol_limit = account.equity * Decimal(str(self.limits.per_symbol_limit_pct / 100))
        return new_symbol_value <= max_symbol_limit

    def _check_exposure_limits(self, order: BacktestOrder, account: BacktestAccount, price: Decimal) -> bool:
        """Check total exposure limits."""
        current_exposure = sum(self.symbol_exposure.values())
        order_value = abs(order.quantity) * price

        if order.side == OrderSide.BUY:
            new_exposure = current_exposure + order_value
        else:
            new_exposure = max(0, current_exposure - order_value)

        max_exposure = account.equity * Decimal(str(self.limits.max_exposure_pct / 100))
        return new_exposure <= max_exposure

    def update_after_trade(self, symbol: str, pnl: Decimal, timestamp: datetime, account: BacktestAccount):
        """Update risk state after a trade."""
        self.daily_pnl += pnl
        self.last_trade_time = timestamp
        self.trade_log.append((timestamp, symbol, pnl))

        # Update drawdown
        if account.equity > self.peak_equity:
            self.peak_equity = account.equity
        if self.peak_equity > 0:
            self.current_drawdown_pct = float(((self.peak_equity - account.equity) / self.peak_equity) * 100)

        # Update symbol exposure
        # Assuming position value update; in real impl, track from account
        self.symbol_exposure[symbol] = account.positions.get(symbol, type('Mock', (), {'quantity': 0, 'avg_price': Decimal('0')})()).quantity * account.positions.get(symbol, type('Mock', (), {'avg_price': Decimal('0')})()).avg_price

        # Check circuit breaker
        if self.current_drawdown_pct >= self.limits.circuit_breaker_threshold_pct:
            self.circuit_breaker_triggered = True

    def _reset_if_new_day(self, current_date: date) -> None:
        """Reset daily state if it's a new trading day."""
        if self.current_day != current_date:
            self.current_day = current_date
            self.daily_pnl = Decimal('0')
            self.trading_disabled = False  # Reset session disable
            # Note: circuit_breaker_triggered persists across days unless manually reset

    def _check_trade_cooldowns(self, timestamp: datetime) -> bool:
        """Check if in cooldown period after a violation."""
        if self.cooldown_until and timestamp < self.cooldown_until:
            return True
        return False

    def _check_daily_loss_limit(self, account: BacktestAccount, current_date: date) -> bool:
        """Check if daily loss limit has been breached."""
        daily_pnl = self.daily_pnl_by_day.get(current_date, Decimal('0'))
        max_loss = account.starting_cash * Decimal(str(self.limits.daily_loss_limit / 100))
        return abs(daily_pnl) <= max_loss

    def _check_position_limits(self, order: BacktestOrder, account: BacktestAccount, price: Decimal) -> bool:
        """Check max positions and per-symbol limits."""
        current_positions = len([p for p in account.positions.values() if p.quantity != 0])

        if order.side == OrderSide.BUY:
            new_positions = current_positions + 1
        else:
            # For sell, check if closing existing
            if order.symbol not in account.positions or account.positions[order.symbol].quantity == 0:
                return True  # Allow short or something, but for simplicity
            new_positions = current_positions

        if new_positions > self.limits.max_positions:
            return False

        # Per-symbol check using new per_symbol_limits
        max_per_symbol = self.limits.per_symbol_limits.get(order.symbol, self.limits.max_positions)
        symbol_positions = sum(1 for pos in account.positions.values() if pos.symbol == order.symbol and pos.quantity != 0)
        if order.side == OrderSide.BUY and symbol_positions >= max_per_symbol:
            return False

        # Exposure cap check
        exposure_cap_pct = self.limits.exposure_caps.get(order.symbol, self.limits.max_exposure_pct)
        current_symbol_exposure = self.symbol_exposure.get(order.symbol, Decimal('0'))
        order_value = abs(order.quantity) * price
        if order.side == OrderSide.BUY:
            new_symbol_exposure = current_symbol_exposure + order_value
        else:
            new_symbol_exposure = max(0, current_symbol_exposure - order_value)

        max_symbol_exposure = account.equity * Decimal(str(exposure_cap_pct / 100))
        return new_symbol_exposure <= max_symbol_exposure

    def _check_exposure_limits(self, order: BacktestOrder, account: BacktestAccount, price: Decimal) -> bool:
        """Check total exposure limits."""
        current_exposure = sum(self.symbol_exposure.values())
        order_value = abs(order.quantity) * price

        if order.side == OrderSide.BUY:
            new_exposure = current_exposure + order_value
        else:
            new_exposure = max(0, current_exposure - order_value)

        max_exposure = account.equity * Decimal(str(self.limits.max_exposure_pct / 100))
        return new_exposure <= max_exposure

    def _apply_position_sizing(self, order: BacktestOrder, account: BacktestAccount, price: Decimal, atr: Optional[float]) -> BacktestOrder:
        """Apply position sizing to the order."""
        # Calculate position size based on sizing method
        size = self.position_sizer.calculate_position_size(order.symbol, price, account, atr)

        # Create a new order with the calculated size
        sized_order = BacktestOrder(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=size,
            price=order.price,
            stop_price=order.stop_price,
            instrument=order.instrument,
            timestamp=order.timestamp
        )

        return sized_order

    def update_after_trade(self, symbol: str, pnl: Decimal, timestamp: datetime, account: BacktestAccount):
        """Update risk state after a trade."""
        trade_date = timestamp.date()
        self.daily_pnl_by_day[trade_date] = self.daily_pnl_by_day.get(trade_date, Decimal('0')) + pnl
        self.last_trade_time = timestamp
        self.trade_log.append((timestamp, symbol, pnl))

        # Update drawdown
        if account.equity > self.peak_equity:
            self.peak_equity = account.equity
        if self.peak_equity > 0:
            self.current_drawdown_pct = float(((self.peak_equity - account.equity) / self.peak_equity) * 100)

        # Update symbol exposure
        # Assuming position value update; in real impl, track from account
        self.symbol_exposure[symbol] = account.positions.get(symbol, type('Mock', (), {'quantity': 0, 'avg_price': Decimal('0')})()).quantity * account.positions.get(symbol, type('Mock', (), {'avg_price': Decimal('0')})()).avg_price

        # Check circuit breaker
        if self.current_drawdown_pct >= self.limits.max_drawdown_stop:
            self.circuit_breaker_triggered = True

    def trigger_cooldown(self, timestamp: datetime) -> None:
        """Trigger cooldown period after a stop-out."""
        self.cooldown_until = timestamp + timedelta(minutes=self.limits.trade_cooldown_minutes)

    def reset_daily(self):
        """Reset daily counters (for multi-day backtests)."""
        self.daily_pnl = Decimal('0')
        self.circuit_breaker_triggered = False
        self.last_trade_time = None
