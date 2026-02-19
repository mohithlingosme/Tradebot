"""
Fill Simulator for Backtesting

Simulates order execution with realistic fills, slippage, and fees.
Supports market, limit, and stop-loss orders.
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum

from common.market_data import Candle
from .costs import CostModel
from .instrument_master import Instrument


@dataclass
class LatencyConfig:
    """Configuration for execution latency simulation."""
    mean_latency_ms: float = 50.0
    std_dev_ms: float = 25.0
    seed: Optional[int] = None  # For reproducible latency in Golden Tests


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LOSS_MARKET = "stop_loss_market"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class BacktestOrder:
    """Order for backtesting."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[Decimal] = None  # For limit/stop orders
    stop_price: Optional[Decimal] = None  # For stop orders
    instrument: Optional[Instrument] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class FillResult:
    """Result of an order fill."""
    order_id: str
    symbol: str
    side: OrderSide
    filled_quantity: int
    fill_price: Decimal
    slippage: Decimal
    fees: Decimal
    timestamp: datetime
    status: OrderStatus = OrderStatus.FILLED


class LatencySimulator:
    """
    Simulates network and execution delays using probability distributions.

    Models realistic "fat-tail" execution delays with log-normal distribution.
    """

    def __init__(self, mean_latency_ms: float = 50.0, std_dev_ms: float = 25.0, seed: Optional[int] = None):
        """
        Initialize latency simulator.

        Args:
            mean_latency_ms: Mean latency in milliseconds
            std_dev_ms: Standard deviation of latency
            seed: Random seed for reproducibility
        """
        self.mean_latency_ms = mean_latency_ms
        self.std_dev_ms = std_dev_ms
        self.rng = np.random.RandomState(seed)

    def simulate_latency(self) -> float:
        """
        Simulate execution latency using log-normal distribution.

        Returns:
            Latency in milliseconds
        """
        # Log-normal distribution for fat-tail delays
        mu = np.log(self.mean_latency_ms**2 / np.sqrt(self.mean_latency_ms**2 + self.std_dev_ms**2))
        sigma = np.sqrt(np.log(1 + (self.std_dev_ms / self.mean_latency_ms)**2))

        return self.rng.lognormal(mu, sigma)

    def get_time_to_fill(self, atr: Optional[float] = None, base_latency: Optional[float] = None) -> float:
        """
        Calculate time-to-fill incorporating volatility.

        Args:
            atr: Average True Range for volatility adjustment
            base_latency: Override base latency

        Returns:
            Time to fill in milliseconds
        """
        base = base_latency or self.simulate_latency()

        if atr:
            # Increase latency for high volatility periods
            volatility_factor = min(atr / 10.0, 5.0)  # Cap at 5x
            base *= (1 + volatility_factor * 0.1)

        return base


class FillSimulator:
    """
    Simulates order fills with realistic execution characteristics.

    Supports different fill models:
    - next_bar_open: Fill at next bar's open price
    - next_tick: Fill at current bar's close + slippage
    - mid_price: Fill at mid of current bar
    """

    def __init__(self, cost_model: CostModel, fill_model: str = "next_bar_open",
                 latency_simulator: Optional[LatencySimulator] = None):
        self.cost_model = cost_model
        self.fill_model = fill_model
        self.latency_simulator = latency_simulator or LatencySimulator()

    def process_market_order(self, order: BacktestOrder, current_candle: Candle,
                           previous_candle: Optional[Candle] = None, atr: Optional[float] = None) -> FillResult:
        """
        Process a market order with latency and volatility-adjusted slippage.

        Fill model determines execution price:
        - next_bar_open: Use next candle's open
        - next_tick: Use current candle's close + slippage
        - mid_price: Use mid of current candle
        """
        if self.fill_model == "next_bar_open":
            if previous_candle is None:
                # No previous candle, use current close
                base_price = current_candle.close
            else:
                base_price = previous_candle.open
        elif self.fill_model == "next_tick":
            base_price = current_candle.close
        elif self.fill_model == "mid_price":
            base_price = (current_candle.high + current_candle.low) / 2
        else:
            base_price = current_candle.close

        # Simulate time-to-fill using latency simulator
        time_to_fill_ms = self.latency_simulator.get_time_to_fill(atr=atr)
        fill_timestamp = current_candle.timestamp + timedelta(milliseconds=time_to_fill_ms)

        # Apply volatility-adjusted slippage
        base_price_decimal = Decimal(str(base_price))

        # Enhanced slippage calculation factoring in time-to-fill and ATR
        slippage_bps = self._calculate_volatility_slippage(time_to_fill_ms, atr or 0.0)
        fill_price = self._apply_slippage_with_atr(
            OrderSide.BUY if order.side == OrderSide.BUY else OrderSide.SELL,
            base_price_decimal,
            slippage_bps
        )

        # Calculate fees
        trade_value = fill_price * abs(order.quantity)
        instrument_type = order.instrument.instrument_type if order.instrument else "cash"
        fees = self.cost_model.total_fees_india(
            instrument_type, trade_value,
            is_intraday=True  # Assume intraday for backtesting
        )

        # Calculate slippage amount
        slippage = abs(fill_price - base_price_decimal) * abs(order.quantity)

        return FillResult(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            filled_quantity=order.quantity,
            fill_price=fill_price,
            slippage=slippage,
            fees=fees,
            timestamp=fill_timestamp
        )

    def _calculate_volatility_slippage(self, time_to_fill_ms: float, atr: float) -> float:
        """
        Calculate slippage in basis points based on time-to-fill and volatility.

        Args:
            time_to_fill_ms: Time to fill in milliseconds
            atr: Average True Range

        Returns:
            Slippage in basis points
        """
        # Base slippage increases with time-to-fill
        base_slippage_bps = min(time_to_fill_ms / 100.0, 50.0)  # Cap at 50bps

        # Add volatility component
        if atr > 0:
            volatility_factor = min(atr / 10.0, 2.0)  # ATR as % of price, cap at 2x
            base_slippage_bps *= (1 + volatility_factor)

        return base_slippage_bps

    def _apply_slippage_with_atr(self, side: OrderSide, base_price: Decimal, slippage_bps: float) -> Decimal:
        """
        Apply slippage to base price.

        Args:
            side: Buy or sell side
            base_price: Base execution price
            slippage_bps: Slippage in basis points

        Returns:
            Adjusted fill price
        """
        slippage_factor = slippage_bps / 10000.0  # Convert bps to decimal

        if side == OrderSide.BUY:
            # Buy orders get worse price (higher)
            return base_price * (1 + Decimal(str(slippage_factor)))
        else:
            # Sell orders get worse price (lower)
            return base_price * (1 - Decimal(str(slippage_factor)))

    def process_limit_order(self, order: BacktestOrder, current_candle: Candle,
                          previous_candle: Optional[Candle] = None) -> Optional[FillResult]:
        """
        Process a limit order.

        Fills if the limit price is reached within the candle.
        """
        if order.price is None:
            return None

        limit_price = order.price

        # Check if limit can be filled in current candle
        if order.side == OrderSide.BUY:
            # Buy limit: price must drop to or below limit
            if current_candle.low <= float(limit_price):
                # Fill at the better of limit price or actual low
                fill_price = min(limit_price, Decimal(str(current_candle.low)))
            else:
                return None  # No fill
        else:  # SELL
            # Sell limit: price must rise to or above limit
            if current_candle.high >= float(limit_price):
                # Fill at the better of limit price or actual high
                fill_price = max(limit_price, Decimal(str(current_candle.high)))
            else:
                return None  # No fill

        # Apply slippage to the fill price
        fill_price = self.cost_model.price_with_slippage(
            OrderSide.BUY if order.side == OrderSide.BUY else OrderSide.SELL,
            fill_price
        )

        # Calculate fees and slippage
        trade_value = fill_price * abs(order.quantity)
        instrument_type = order.instrument.instrument_type if order.instrument else "cash"
        fees = self.cost_model.total_fees_india(
            instrument_type, trade_value, is_intraday=True
        )

        base_price = limit_price  # Slippage relative to limit price
        slippage = abs(fill_price - base_price) * abs(order.quantity)

        return FillResult(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            filled_quantity=order.quantity,
            fill_price=fill_price,
            slippage=slippage,
            fees=fees,
            timestamp=current_candle.timestamp
        )

    def process_stop_order(self, order: BacktestOrder, current_candle: Candle,
                         previous_candle: Optional[Candle] = None, atr: Optional[float] = None) -> Optional[FillResult]:
        """
        Process a stop-loss order.

        For stop-loss: triggers when price moves against position
        For stop-loss-market: triggers and fills at market
        """
        if order.stop_price is None:
            return None

        stop_price = order.stop_price
        triggered = False

        if order.side == OrderSide.BUY:
            # Buy stop: triggers when price rises above stop
            if current_candle.high >= float(stop_price):
                triggered = True
        else:  # SELL
            # Sell stop: triggers when price falls below stop
            if current_candle.low <= float(stop_price):
                triggered = True

        if not triggered:
            return None

        # For stop-loss-market, fill at market
        if order.order_type == OrderType.STOP_LOSS_MARKET:
            return self.process_market_order(order, current_candle, previous_candle, atr)
        else:
            # For regular stop-loss, fill at stop price (treated as limit)
            order.price = stop_price
            return self.process_limit_order(order, current_candle, previous_candle)

    def process_order(self, order: BacktestOrder, current_candle: Candle,
                    previous_candle: Optional[Candle] = None) -> Optional[FillResult]:
        """
        Process any type of order and return fill result if filled.
        """
        if order.order_type == OrderType.MARKET:
            return self.process_market_order(order, current_candle, previous_candle)
        elif order.order_type == OrderType.LIMIT:
            return self.process_limit_order(order, current_candle, previous_candle)
        elif order.order_type in [OrderType.STOP_LOSS, OrderType.STOP_LOSS_MARKET]:
            return self.process_stop_order(order, current_candle, previous_candle)
        else:
            raise ValueError(f"Unsupported order type: {order.order_type}")

    def simulate_partial_fills(self, order: BacktestOrder, current_candle: Candle,
                             max_partial_fills: int = 3) -> List[FillResult]:
        """
        Simulate partial fills for large orders.

        Breaks large orders into smaller fills across multiple candles.
        """
        if abs(order.quantity) <= 1000:  # Small order, fill completely
            result = self.process_order(order, current_candle)
            return [result] if result else []

        # Large order - simulate partial fills
        fills = []
        remaining_qty = order.quantity
        fill_count = min(max_partial_fills, abs(order.quantity) // 500)  # Fill in chunks of ~500

        for i in range(fill_count):
            if remaining_qty == 0:
                break

            # Create partial order
            partial_qty = remaining_qty // (fill_count - i)
            partial_order = BacktestOrder(
                order_id=f"{order.order_id}_partial_{i}",
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=partial_qty,
                price=order.price,
                stop_price=order.stop_price,
                instrument=order.instrument,
                timestamp=order.timestamp
            )

            # Process partial fill
            fill_result = self.process_order(partial_order, current_candle)
            if fill_result:
                fills.append(fill_result)
                remaining_qty -= partial_qty

        return fills

    def get_fill_statistics(self, fills: List[FillResult]) -> Dict[str, Any]:
        """Calculate fill statistics."""
        if not fills:
            return {}

        total_quantity = sum(abs(f.filled_quantity) for f in fills)
        total_slippage = sum(f.slippage for f in fills)
        total_fees = sum(f.fees for f in fills)

        avg_slippage_per_unit = total_slippage / total_quantity if total_quantity > 0 else 0
        avg_fees_per_unit = total_fees / total_quantity if total_quantity > 0 else 0

        return {
            "total_fills": len(fills),
            "total_quantity": total_quantity,
            "total_slippage": float(total_slippage),
            "total_fees": float(total_fees),
            "avg_slippage_per_unit": float(avg_slippage_per_unit),
            "avg_fees_per_unit": float(avg_fees_per_unit),
            "slippage_to_fees_ratio": float(total_slippage / total_fees) if total_fees > 0 else 0
        }


# Example usage
if __name__ == "__main__":
    from .costs import CostModel

    cost_model = CostModel()
    simulator = FillSimulator(cost_model, fill_model="next_bar_open")

    # Create sample order
    order = BacktestOrder(
        order_id="test_001",
        symbol="RELIANCE",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=100
    )

    # Create sample candle
    from datetime import datetime, timezone
    candle = Candle(
        symbol="RELIANCE",
        timestamp=datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc),
        open=2500.0,
        high=2520.0,
        low=2490.0,
        close=2510.0,
        volume=10000,
        timeframe="1m"
    )

    # Process order
    fill_result = simulator.process_order(order, candle)
    if fill_result:
        print(f"Order filled: {fill_result.filled_quantity} @ {fill_result.fill_price}")
        print(f"Slippage: {fill_result.slippage}, Fees: {fill_result.fees}")
    else:
        print("Order not filled")
