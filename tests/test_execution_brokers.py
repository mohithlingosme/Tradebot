from execution.mocked_broker import MockedBroker
from execution.base_broker import Order, OrderSide, OrderType, OrderStatus


def test_mock_broker_fills_market_orders():
    broker = MockedBroker(starting_cash=10_000)
    order = Order(
        id=None,
        symbol="TEST",
        side=OrderSide.BUY,
        quantity=10,
        order_type=OrderType.MARKET,
        price=100.0,
    )

    filled = broker.place_order(order)
    assert filled.status == OrderStatus.FILLED
    assert filled.filled_quantity == 10
    assert filled.avg_fill_price == 100.0
    assert broker.get_balance().available < 10_000


def test_mock_broker_cancel():
    broker = MockedBroker(starting_cash=10_000)
    order = Order(
        id=None,
        symbol="TEST",
        side=OrderSide.BUY,
        quantity=1,
        order_type=OrderType.MARKET,
        price=1.0,
    )
    filled = broker.place_order(order)
    # Can't cancel filled orders
    assert not broker.cancel_order(filled.id)
    # Unknown orders also false
    assert not broker.cancel_order("missing")

