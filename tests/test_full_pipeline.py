from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from common.market_data import Candle
from execution.base_broker import Order, OrderSide, OrderStatus, OrderType
from execution.mocked_broker import MockedBroker
from risk.risk_manager import AccountState, MarginCalculator, OrderRequest, RiskLimits, RiskManager
from strategies.ema_crossover.strategy import EMACrossoverConfig, EMACrossoverStrategy


def _intraday_candles(symbol: str, total: int = 120) -> Tuple[List[Candle], List[float]]:
    """
    Build a synthetic intraday session:
    - slow rise then slow fall to trigger EMA crossover entry and exit.
    """
    start = datetime(2024, 1, 1, 9, 15, tzinfo=timezone.utc)
    rise = [100 + i * 0.2 for i in range(total // 2)]
    fall = [rise[-1] - i * 0.25 for i in range(total - len(rise))]
    prices = rise + fall
    candles = []
    for idx, price in enumerate(prices):
        ts = start + timedelta(minutes=idx)
        candles.append(
            Candle(
                symbol=symbol,
                timestamp=ts,
                open=price,
                high=price + 0.1,
                low=price - 0.1,
                close=price,
                volume=10_000,
                source="synthetic",
                timeframe="1m",
            )
        )
    return candles, prices


def _current_equity(broker: MockedBroker, mark_price: float) -> float:
    cash = broker.get_balance().available
    positions_value = sum(pos.quantity * mark_price for pos in broker.list_positions())
    return cash + positions_value


def test_full_pipeline_intraday_ema_with_mock_broker():
    symbol = "NIFTY"
    candles, prices = _intraday_candles(symbol)

    strategy = EMACrossoverStrategy(EMACrossoverConfig(short_window=5, long_window=15, timeframe="1m", symbol_universe=[symbol]))
    limits = RiskLimits(max_daily_loss_pct=0.05, max_open_positions=3, max_risk_per_trade_pct=0.01, max_margin_utilization_pct=1.0)
    margin_calc = MarginCalculator(intraday_leverage=5.0, carry_leverage=1.0)
    risk_manager = RiskManager(limits=limits, margin_calculator=margin_calc)
    broker = MockedBroker(starting_cash=100_000.0)

    starting_equity = _current_equity(broker, prices[0])
    executed_orders: List[Order] = []
    buys = sells = 0

    for candle in candles:
        # Update account snapshot and risk manager
        open_positions = sum(1 for pos in broker.list_positions() if pos.quantity > 0)
        equity = _current_equity(broker, candle.close)
        todays_pnl = equity - starting_equity
        state = AccountState(
            equity=equity,
            todays_pnl=todays_pnl,
            open_positions_count=open_positions,
            available_margin=equity,
        )
        risk_manager.update_account_state(state)

        # Feed strategy and emit signals
        strategy.update(candle)
        sig = strategy.signal()
        if sig == "NONE":
            continue

        side = OrderSide.BUY if sig == "BUY" else OrderSide.SELL
        order_req = OrderRequest(
            symbol=candle.symbol,
            side=side.value,
            qty=50,
            price=candle.close,
            product_type="INTRADAY",
            instrument_type="EQUITY",
            stop_price=candle.close * (0.985 if side == OrderSide.BUY else 1.015),
            lot_size=1,
            reduces_position=side == OrderSide.SELL,
        )

        allowed, reason = risk_manager.validate_order(state, order_req)
        assert allowed, f"Order should be allowed during benign scenario: {reason}"

        order = Order(
            id=None,
            symbol=order_req.symbol,
            side=OrderSide(order_req.side),
            quantity=order_req.qty,
            order_type=OrderType.MARKET,
            price=order_req.price,
        )
        filled = broker.place_order(order)
        executed_orders.append(filled)
        if filled.side == OrderSide.BUY:
            buys += 1
        else:
            sells += 1

        # Assert fills are immediate and status is FILLED
        assert filled.status == OrderStatus.FILLED

    # Final MTM check and cleanup
    # Flatten any residual exposure at session end
    remaining_positions = [pos for pos in broker.list_positions() if pos.quantity > 0]
    if remaining_positions:
        pos = remaining_positions[0]
        flat_order = Order(
            id=None,
            symbol=pos.symbol,
            side=OrderSide.SELL,
            quantity=pos.quantity,
            order_type=OrderType.MARKET,
            price=prices[-1],
        )
        broker.place_order(flat_order)
        executed_orders.append(flat_order)
        sells += 1

    final_equity = _current_equity(broker, prices[-1])

    assert buys >= 1
    assert sells >= 1  # should have flattened on crossover down
    assert risk_manager.circuit_breaker_triggered is False
    assert all(pos.quantity == 0 for pos in broker.list_positions())
    assert final_equity > starting_equity * 0.9
    assert final_equity < starting_equity * 1.5
    assert any(o.status == OrderStatus.FILLED for o in executed_orders)
