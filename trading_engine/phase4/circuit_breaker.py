"""
Circuit breaker utilities for trading safety.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from .models import CircuitBreakerState


@dataclass
class CircuitBreakerConfig:
    max_consecutive_losses: int = 3
    max_drawdown_pct: float = 0.05
    cooldown_seconds: int = 300


class StrategyCircuitBreaker:
    """Per-strategy breaker based on losses and drawdown."""

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.ARMED
        self.consecutive_losses = 0
        self.peak_equity: Optional[float] = None
        self.triggered_at: Optional[datetime] = None

    def record_trade(self, pnl: float, equity: float) -> None:
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        if self.peak_equity is None or equity > self.peak_equity:
            self.peak_equity = equity

        drawdown = 0.0
        if self.peak_equity and self.peak_equity > 0:
            drawdown = (self.peak_equity - equity) / self.peak_equity

        if (
            self.consecutive_losses >= self.config.max_consecutive_losses
            or drawdown >= self.config.max_drawdown_pct
        ):
            self.state = CircuitBreakerState.TRIGGERED
            self.triggered_at = datetime.now(timezone.utc)

    def can_trade(self) -> bool:
        if self.state == CircuitBreakerState.ARMED:
            return True
        if self.state == CircuitBreakerState.TRIGGERED and self.triggered_at:
            cooldown_over = datetime.now(timezone.utc) - self.triggered_at > timedelta(seconds=self.config.cooldown_seconds)
            if cooldown_over:
                self.reset()
                return True
        return False

    def reset(self) -> None:
        self.state = CircuitBreakerState.RESET
        self.consecutive_losses = 0
        self.triggered_at = None
        self.peak_equity = None
        self.state = CircuitBreakerState.ARMED


@dataclass
class GlobalCircuitBreakerConfig:
    daily_loss_limit_pct: float = 0.08
    max_drawdown_pct: float = 0.2
    cooldown_seconds: int = 900


class GlobalCircuitBreaker:
    """Portfolio-wide breaker for daily loss and drawdown."""

    def __init__(self, config: Optional[GlobalCircuitBreakerConfig] = None):
        self.config = config or GlobalCircuitBreakerConfig()
        self.state = CircuitBreakerState.ARMED
        self.peak_equity: Optional[float] = None
        self.session_start_equity: Optional[float] = None
        self.triggered_at: Optional[datetime] = None

    def observe(self, equity: float) -> None:
        if self.session_start_equity is None:
            self.session_start_equity = equity
        if self.peak_equity is None or equity > self.peak_equity:
            self.peak_equity = equity

        drawdown = 0.0
        if self.peak_equity and self.peak_equity > 0:
            drawdown = (self.peak_equity - equity) / self.peak_equity

        daily_loss = 0.0
        if self.session_start_equity and self.session_start_equity > 0:
            daily_loss = (self.session_start_equity - equity) / self.session_start_equity

        if drawdown >= self.config.max_drawdown_pct or daily_loss >= self.config.daily_loss_limit_pct:
            self.state = CircuitBreakerState.TRIGGERED
            self.triggered_at = datetime.now(timezone.utc)

    def can_trade(self) -> bool:
        if self.state == CircuitBreakerState.ARMED:
            return True
        if self.state == CircuitBreakerState.TRIGGERED and self.triggered_at:
            if datetime.now(timezone.utc) - self.triggered_at > timedelta(seconds=self.config.cooldown_seconds):
                self.reset()
                return True
        return False

    def reset(self) -> None:
        self.state = CircuitBreakerState.RESET
        self.triggered_at = None
        self.peak_equity = None
        self.session_start_equity = None
        self.state = CircuitBreakerState.ARMED
