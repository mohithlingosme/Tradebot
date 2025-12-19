from datetime import datetime, timezone

from strategies.order_book_imbalance.strategy import (
    OrderBookImbalanceConfig,
    OrderBookImbalanceStrategy,
)


class MockOrderBookFeed:
    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.pointer = 0

    def get_latest_order_book(self, symbol):
        if self.pointer >= len(self.snapshots):
            return None
        snapshot = self.snapshots[self.pointer]
        self.pointer += 1
        snapshot["symbol"] = symbol
        snapshot["timestamp"] = datetime.now(timezone.utc)
        return snapshot


def _snapshot(imbalance: float):
    base_price = 100.0
    buy = 100 * (1 + imbalance)
    sell = 100 * (1 - imbalance)
    bids = [{"price": base_price - 0.1 * i, "size": buy / 5} for i in range(5)]
    asks = [{"price": base_price + 0.1 * i, "size": sell / 5} for i in range(5)]
    return {"bids": bids, "asks": asks}


def test_order_book_imbalance_strategy_generates_signals():
    feed = MockOrderBookFeed(
        [
            _snapshot(0.3),  # Buy signal
            _snapshot(0.1),  # Hold
            _snapshot(-0.4),  # Sell signal
            _snapshot(0.0),  # Exit
        ]
    )
    strategy = OrderBookImbalanceStrategy(
        feed, OrderBookImbalanceConfig(symbol="BTCUSD", entry_threshold=0.2, cooldown_seconds=0)
    )

    signal = strategy.next()
    assert signal["action"] == "BUY"

    signal = strategy.next()
    assert signal["action"] == "HOLD"

    signal = strategy.next()
    assert signal["action"] == "SELL"

    signal = strategy.next()
    assert signal["action"] == "BUY"
