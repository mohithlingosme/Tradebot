"""
Backtesting Account Model

Handles account state, margin calculations, and position management for backtesting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional, Any
from datetime import datetime

from .instrument_master import Instrument


@dataclass
class BacktestPosition:
    """Position in a backtest account."""
    symbol: str
    quantity: int
    average_price: Decimal
    current_price: Optional[Decimal] = None
    unrealized_pnl: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')
    instrument: Optional[Instrument] = None

    @property
    def market_value(self) -> Decimal:
        """Current market value of the position."""
        if self.current_price is None:
            return Decimal('0')
        return self.current_price * abs(self.quantity)

    @property
    def total_pnl(self) -> Decimal:
        """Total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    def update_pnl(self, current_price: Decimal) -> None:
        """Update unrealized P&L based on current price."""
        self.current_price = current_price
        if self.quantity != 0:
            self.unrealized_pnl = (current_price - self.average_price) * self.quantity


@dataclass
class BacktestAccount:
    """
    Account model for backtesting with margin and leverage support.

    Supports both cash and margin accounts with F&O margin calculations.
    """

    # Basic account info
    account_id: str
    currency: str = "INR"

    # Capital
    starting_cash: Decimal = Decimal('100000')
    cash_balance: Decimal = field(init=False)
    margin_available: Decimal = Decimal('0')

    # Margin settings
    leverage: Decimal = Decimal('1')  # 1 = no leverage, 2 = 2x leverage
    margin_call_threshold: Decimal = Decimal('0.25')  # 25% of equity
    liquidation_threshold: Decimal = Decimal('0.10')  # 10% of equity

    # Positions
    positions: Dict[str, BacktestPosition] = field(default_factory=dict)

    # P&L tracking
    total_realized_pnl: Decimal = Decimal('0')
    total_unrealized_pnl: Decimal = Decimal('0')

    # Trading costs
    total_fees: Decimal = Decimal('0')
    total_slippage: Decimal = Decimal('0')

    # Risk metrics
    peak_equity: Decimal = field(init=False)
    max_drawdown: Decimal = Decimal('0')
    max_drawdown_pct: Decimal = Decimal('0')

    # Trading stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    def __post_init__(self):
        self.cash_balance = self.starting_cash
        self.peak_equity = self.equity

    @property
    def equity(self) -> Decimal:
        """Total account equity (cash + unrealized P&L)."""
        return self.cash_balance + self.total_unrealized_pnl

    @property
    def gross_exposure(self) -> Decimal:
        """Total gross exposure across all positions."""
        return sum(abs(pos.market_value) for pos in self.positions.values())

    @property
    def net_exposure(self) -> Decimal:
        """Net exposure (long - short positions)."""
        net = Decimal('0')
        for pos in self.positions.values():
            net += pos.market_value
        return net

    @property
    def margin_used(self) -> Decimal:
        """Margin currently used by positions."""
        margin_used = Decimal('0')
        for pos in self.positions.values():
            if pos.instrument and pos.instrument.instrument_type in ['futures', 'options']:
                # For F&O, margin is based on SPAN margin (simplified)
                margin_used += abs(pos.market_value) * Decimal('0.20')  # 20% margin
            else:
                # For cash equity, full value
                margin_used += abs(pos.market_value)
        return margin_used

    @property
    def buying_power(self) -> Decimal:
        """Available buying power considering leverage."""
        max_exposure = (self.equity + self.margin_available) * self.leverage
        used_exposure = self.margin_used
        return max(Decimal('0'), max_exposure - used_exposure)

    @property
    def margin_utilization(self) -> Decimal:
        """Current margin utilization percentage."""
        if self.equity + self.margin_available <= 0:
            return Decimal('1')
        return self.margin_used / ((self.equity + self.margin_available) * self.leverage)

    def update_positions_pnl(self, prices: Dict[str, Decimal]) -> None:
        """Update P&L for all positions based on current prices."""
        total_unrealized = Decimal('0')
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_pnl(price)
                total_unrealized += self.positions[symbol].unrealized_pnl

        self.total_unrealized_pnl = total_unrealized

        # Update drawdown
        current_equity = self.equity
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        else:
            drawdown = self.peak_equity - current_equity
            drawdown_pct = drawdown / self.peak_equity if self.peak_equity > 0 else Decimal('0')
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
                self.max_drawdown_pct = drawdown_pct

    def check_margin_call(self) -> bool:
        """Check if account is in margin call territory."""
        if self.equity <= 0:
            return True

        equity_pct = self.equity / self.starting_cash
        return equity_pct <= self.margin_call_threshold

    def check_liquidation(self) -> bool:
        """Check if account should be liquidated."""
        if self.equity <= 0:
            return True

        equity_pct = self.equity / self.starting_cash
        return equity_pct <= self.liquidation_threshold

    def add_position(self, symbol: str, quantity: int, price: Decimal,
                    instrument: Optional[Instrument] = None) -> bool:
        """
        Add or update a position.

        Returns True if successful, False if insufficient funds.
        """
        trade_value = abs(price * quantity)

        # Check if we have sufficient buying power
        if trade_value > self.buying_power:
            return False

        if symbol not in self.positions:
            self.positions[symbol] = BacktestPosition(
                symbol=symbol,
                quantity=0,
                average_price=Decimal('0'),
                instrument=instrument
            )

        position = self.positions[symbol]

        # Calculate new average price
        if position.quantity == 0:
            new_avg_price = price
        elif (position.quantity > 0 and quantity > 0) or (position.quantity < 0 and quantity < 0):
            # Same direction - average up/down
            total_qty = position.quantity + quantity
            total_value = (position.average_price * position.quantity) + (price * quantity)
            new_avg_price = total_value / total_qty
        else:
            # Opposite direction - may close or reduce position
            new_avg_price = position.average_price

        position.quantity += quantity
        position.average_price = new_avg_price

        # If position is closed, realize P&L
        if position.quantity == 0:
            position.realized_pnl += position.unrealized_pnl
            position.unrealized_pnl = Decimal('0')
            self.total_realized_pnl += position.realized_pnl

        # Update trade stats
        self.total_trades += 1

        return True

    def remove_position(self, symbol: str) -> None:
        """Remove a position (force close)."""
        if symbol in self.positions:
            position = self.positions[symbol]
            # Realize any remaining P&L
            self.total_realized_pnl += position.unrealized_pnl
            del self.positions[symbol]

    def apply_fees_and_slippage(self, fees: Decimal, slippage: Decimal) -> None:
        """Apply trading fees and slippage to account."""
        self.total_fees += fees
        self.total_slippage += slippage
        self.cash_balance -= (fees + slippage)

    def deposit(self, amount: Decimal) -> None:
        """Add cash to account."""
        self.cash_balance += amount

    def withdraw(self, amount: Decimal) -> None:
        """Remove cash from account."""
        if amount <= self.cash_balance:
            self.cash_balance -= amount

    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions."""
        return {
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_price": float(pos.average_price),
                    "current_price": float(pos.current_price) if pos.current_price else None,
                    "market_value": float(pos.market_value),
                    "unrealized_pnl": float(pos.unrealized_pnl),
                    "realized_pnl": float(pos.realized_pnl),
                    "total_pnl": float(pos.total_pnl)
                }
                for pos in self.positions.values()
            ],
            "total_positions": len(self.positions),
            "gross_exposure": float(self.gross_exposure),
            "net_exposure": float(self.net_exposure)
        }

    def get_account_summary(self) -> Dict[str, Any]:
        """Get comprehensive account summary."""
        return {
            "account_id": self.account_id,
            "currency": self.currency,
            "starting_cash": float(self.starting_cash),
            "cash_balance": float(self.cash_balance),
            "equity": float(self.equity),
            "margin_available": float(self.margin_available),
            "margin_used": float(self.margin_used),
            "margin_utilization": float(self.margin_utilization),
            "buying_power": float(self.buying_power),
            "leverage": float(self.leverage),
            "total_realized_pnl": float(self.total_realized_pnl),
            "total_unrealized_pnl": float(self.total_unrealized_pnl),
            "total_fees": float(self.total_fees),
            "total_slippage": float(self.total_slippage),
            "peak_equity": float(self.peak_equity),
            "max_drawdown": float(self.max_drawdown),
            "max_drawdown_pct": float(self.max_drawdown_pct),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "margin_call": self.check_margin_call(),
            "liquidation": self.check_liquidation()
        }


# Example usage
if __name__ == "__main__":
    account = BacktestAccount(
        account_id="test_account",
        starting_cash=Decimal('100000'),
        leverage=Decimal('2')
    )

    print(f"Initial equity: {account.equity}")
    print(f"Buying power: {account.buying_power}")

    # Add a position
    success = account.add_position("RELIANCE", 10, Decimal('2500'))
    if success:
        print("Position added successfully")
        print(f"New equity: {account.equity}")
        print(f"Margin used: {account.margin_used}")
    else:
        print("Insufficient funds")

    # Update prices
    account.update_positions_pnl({"RELIANCE": Decimal('2550')})
    print(f"After price update - Equity: {account.equity}")

    print("Account summary:", account.get_account_summary())
