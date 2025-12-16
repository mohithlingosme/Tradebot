import unittest
from execution.engine import ExecutionEngine, OrderSide, OrderType, OrderStatus, Order


class TestExecutionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ExecutionEngine(paper_trading=True)

    def test_place_market_order_buy(self):
        order_id = self.engine.place_order("INFY", 10, OrderSide.BUY, OrderType.MARKET)
        order = self.engine.get_order(order_id)
        self.assertIsNotNone(order)
        self.assertEqual(order.symbol, "INFY")
        self.assertEqual(order.qty, 10)
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.order_type, OrderType.MARKET)
        self.assertEqual(order.status, OrderStatus.FILLED)
        self.assertIsNotNone(order.fill_price)
        self.assertIsNotNone(order.slippage)

    def test_place_limit_order_sell(self):
        order_id = self.engine.place_order("INFY", 5, OrderSide.SELL, OrderType.LIMIT, price=1500.0)
        order = self.engine.get_order(order_id)
        self.assertIsNotNone(order)
        self.assertEqual(order.symbol, "INFY")
        self.assertEqual(order.qty, 5)
        self.assertEqual(order.side, OrderSide.SELL)
        self.assertEqual(order.order_type, OrderType.LIMIT)
        self.assertEqual(order.price, 1500.0)
        self.assertEqual(order.status, OrderStatus.FILLED)
        self.assertEqual(order.fill_price, 1500.0)  # Should match limit price
        self.assertEqual(order.slippage, 0.0)

    def test_cancel_pending_order(self):
        # For this test, we need to simulate a pending order
        # Since paper trading fills immediately, we'll modify the engine temporarily
        order_id = str(uuid.uuid4())
        order = Order(
            order_id=order_id,
            symbol="INFY",
            qty=10,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=1500.0,
            status=OrderStatus.PENDING
        )
        self.engine.orders[order_id] = order

        success = self.engine.cancel_order(order_id)
        self.assertTrue(success)
        self.assertEqual(order.status, OrderStatus.CANCELLED)

    def test_modify_order_price(self):
        # Create a pending order
        order_id = str(uuid.uuid4())
        order = Order(
            order_id=order_id,
            symbol="INFY",
            qty=10,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=1500.0,
            status=OrderStatus.PENDING
        )
        self.engine.orders[order_id] = order

        success = self.engine.modify_order(order_id, 1510.0)
        self.assertTrue(success)
        self.assertEqual(order.price, 1510.0)

    def test_position_update_buy(self):
        initial_position = self.engine.positions.get("INFY", 0)
        order_id = self.engine.place_order("INFY", 10, OrderSide.BUY, OrderType.MARKET)
        final_position = self.engine.positions.get("INFY", 0)
        self.assertEqual(final_position, initial_position + 10)

    def test_position_update_sell(self):
        # First buy some shares
        self.engine.place_order("INFY", 20, OrderSide.BUY, OrderType.MARKET)
        initial_position = self.engine.positions.get("INFY", 0)
        order_id = self.engine.place_order("INFY", 5, OrderSide.SELL, OrderType.MARKET)
        final_position = self.engine.positions.get("INFY", 0)
        self.assertEqual(final_position, initial_position - 5)

    def test_get_nonexistent_order(self):
        order = self.engine.get_order("nonexistent")
        self.assertIsNone(order)


if __name__ == '__main__':
    unittest.main()
