from __future__ import annotations

"""
Lightweight risk engine for backtests and paper trading.

This module focuses on simple capital-based limits (risk per trade, daily loss,
lot-size bounds, trade counts). It is intentionally narrower than
`risk/risk_manager.py`, which targets live trading integrations.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Dict, List
from decimal import Decimal
from enum import Enum


class PositionSizingMethod(Enum):
    FIXED = "fixed"
    PERCENT_EQUITY = "percent_equity"
    ATR_VOLATILITY = "atr_volatility"


class CircuitBreakerType(Enum):
    DAILY_LOSS = "daily_loss"
    MAX_DRAWDOWN = "max_drawdown"


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

    # Position sizing
    position_sizing_method: PositionSizingMethod = PositionSizingMethod.FIXED
    fixed_position_size: int = 100
    percent_equity_risk: float = 0.01  # 1% of equity per trade
    atr_multiplier: float = 2.0  # ATR multiplier for volatility sizing

    # Exposure caps
    max_positions_global: int = 10
    max_positions_per_symbol: int = 3
    max_exposure_percent: float = 0.20  # 20% max exposure per symbol

    # Hard stops
    circuit_breaker_enabled: bool = True
    max_drawdown_limit: float = 0.10  # 10% max drawdown
    daily_loss_hard_stop: float = 0.05  # 5% daily loss hard stop

    # Cooldown
    cooldown_period_minutes: int = 5
    last_trade_time: Optional[datetime] = None

    # State tracking
    open_positions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    symbol_exposure: Dict[str, float] = field(default_factory=dict)
    peak_equity: float = field(init=False)
    current_drawdown: float = 0.0
    trading_disabled: bool = False
    cooldown_until: Optional[datetime] = None

    def __post_init__(self):
        self.peak_equity = self.capital

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

    def calculate_position_size(self, symbol: str, entry_price: float, stop_price: Optional[float] = None,
                               atr: Optional[float] = None) -> int:
        """
        Calculate position size based on configured method.

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_price: Stop loss price
            atr: Average True Range for volatility sizing

        Returns:
            Position size in shares/contracts
        """
        if self.position_sizing_method == PositionSizingMethod.FIXED:
            return self.fixed_position_size

        elif self.position_sizing_method == PositionSizingMethod.PERCENT_EQUITY:
            risk_amount = self.capital * self.percent_equity_risk
            if stop_price:
                stop_distance = abs(entry_price - stop_price)
                if stop_distance > 0:
                    return int(risk_amount / stop_distance)
            return self.fixed_position_size  # Fallback

        elif self.position_sizing_method == PositionSizingMethod.ATR_VOLATILITY:
            if atr and atr > 0:
                risk_amount = self.capital * self.percent_equity_risk
                stop_distance = atr * self.atr_multiplier
                return int(risk_amount / stop_distance)
            return self.fixed_position_size  # Fallback

        return self.fixed_position_size

    def check_exposure_limits(self, symbol: str, proposed_size: int, entry_price: float) -> bool:
        """
        Check if proposed trade violates exposure limits.

        Args:
            symbol: Trading symbol
            proposed_size: Proposed position size
            entry_price: Entry price

        Returns:
            True if within limits, False if violated
        """
        # Global position limit
        if len(self.open_positions) >= self.max_positions_global:
            return False

        # Per-symbol position limit
        symbol_positions = sum(1 for pos in self.open_positions.values() if pos.get('symbol') == symbol)
        if symbol_positions >= self.max_positions_per_symbol:
            return False

        # Exposure percentage limit
        proposed_exposure = proposed_size * entry_price
        max_allowed_exposure = self.capital * self.max_exposure_percent
        current_symbol_exposure = self.symbol_exposure.get(symbol, 0.0)

        if current_symbol_exposure + proposed_exposure > max_allowed_exposure:
            return False

        return True

    def check_circuit_breakers(self, current_equity: float, timestamp: datetime) -> bool:
        """
        Check if circuit breakers should disable trading.

        Args:
            current_equity: Current portfolio equity
            timestamp: Current timestamp

        Returns:
            True if trading allowed, False if disabled
        """
        if not self.circuit_breaker_enabled:
            return True

        # Update drawdown
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity

        # Max drawdown circuit breaker
        if self.current_drawdown >= self.max_drawdown_limit:
            self.trading_disabled = True
            return False

        # Daily loss hard stop (reset at start of day)
        current_date = timestamp.date()
        if current_date != self.current_day:
            self.current_day = current_date
            self.current_day_pnl = 0.0
            self.trading_disabled = False  # Reset daily circuit breaker

        daily_loss_pct = abs(self.current_day_pnl) / self.capital if self.capital > 0 else 0
        if daily_loss_pct >= self.daily_loss_hard_stop:
            self.trading_disabled = True
            return False

        return not self.trading_disabled

    def check_cooldown(self, timestamp: datetime) -> bool:
        """
        Check if in cooldown period after a violation.

        Args:
            timestamp: Current timestamp

        Returns:
            True if cooldown active, False if can trade
        """
        if self.cooldown_until and timestamp < self.cooldown_until:
            return True
        return False

    def trigger_cooldown(self, timestamp: datetime) -> None:
        """
        Trigger cooldown period after a violation.

        Args:
            timestamp: Current timestamp
        """
        from datetime import timedelta
        self.cooldown_until = timestamp + timedelta(minutes=self.cooldown_period_minutes)

    def update_position(self, symbol: str, size: int, entry_price: float) -> None:
        """
        Update position tracking after opening a trade.

        Args:
            symbol: Trading symbol
            size: Position size
            entry_price: Entry price
        """
        if symbol not in self.open_positions:
            self.open_positions[symbol] = {
                'symbol': symbol,
                'size': 0,
                'entry_price': entry_price,
                'entry_time': datetime.utcnow()
            }

        self.open_positions[symbol]['size'] += size
        exposure = abs(size) * entry_price
        self.symbol_exposure[symbol] = self.symbol_exposure.get(symbol, 0.0) + exposure

    def close_position(self, symbol: str) -> None:
        """
        Remove position tracking after closing a trade.

        Args:
            symbol: Trading symbol
        """
        if symbol in self.open_positions:
            del self.open_positions[symbol]
        if symbol in self.symbol_exposure:
            del self.symbol_exposure[symbol]

    def can_open_trade_enhanced(self, symbol: str, entry_price: float, stop_price: Optional[float],
                               atr: Optional[float], current_equity: float, timestamp: datetime) -> tuple[bool, int]:
        """
        Enhanced trade approval with all risk checks.

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_price: Stop loss price
            atr: Average True Range
            current_equity: Current portfolio equity
            timestamp: Current timestamp

        Returns:
            Tuple of (approved: bool, position_size: int)
        """
        # Check circuit breakers
        if not self.check_circuit_breakers(current_equity, timestamp):
            return False, 0

        # Check cooldown
        if self.check_cooldown(timestamp):
            return False, 0

        # Calculate position size
        position_size = self.calculate_position_size(symbol, entry_price, stop_price, atr)

        # Check exposure limits
        if not self.check_exposure_limits(symbol, position_size, entry_price):
            return False, 0

        # Calculate stop distance for risk check
        stop_distance = abs(entry_price - stop_price) if stop_price else entry_price * 0.01  # 1% default

        # Legacy risk checks
        if not self.can_open_trade(position_size, stop_distance):
            return False, 0

        return True, position_size
