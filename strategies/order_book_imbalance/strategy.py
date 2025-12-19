from __future__ import annotations

"""Order book imbalance based microstructure strategy."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from strategies.base import Signal, Strategy
from strategies.registry import registry


@dataclass
class OrderBookImbalanceConfig:
    symbol: str = "BTC-USD"
    depth: int = 5
    entry_threshold: float = 0.25
    exit_threshold: float = 0.05
    cooldown_seconds: int = 15


class OrderBookImbalanceStrategy(Strategy):
    """Generate signals when bid/ask liquidity becomes skewed."""

    def __init__(self, data_feed, config: OrderBookImbalanceConfig | Dict[str, Any] | None = None) -> None:
        super().__init__(data_feed)
        cfg = config or OrderBookImbalanceConfig()
        if isinstance(cfg, dict):
            cfg = OrderBookImbalanceConfig(**cfg)
        self.config = cfg
        self.state.update(
            {
                "position": "flat",
                "last_signal_at": None,
            }
        )

    def next(self) -> Signal:
        snapshot = self._latest_snapshot()
        if snapshot is None:
            return {"action": "HOLD"}

        now = snapshot["timestamp"]
        if self._in_cooldown(now):
            return {"action": "HOLD"}

        imbalance = snapshot["imbalance"]
        metadata = {
            "symbol": snapshot["symbol"],
            "imbalance": imbalance,
            "buy_pressure": snapshot["buy_pressure"],
            "sell_pressure": snapshot["sell_pressure"],
        }

        if imbalance >= self.config.entry_threshold and self.state["position"] != "long":
            self.state["position"] = "long"
            self.state["last_signal_at"] = now
            return {
                "action": "BUY",
                "symbol": snapshot["symbol"],
                "price": snapshot["mid_price"],
                "type": "MARKET",
                "metadata": metadata,
            }
        if imbalance <= -self.config.entry_threshold and self.state["position"] != "short":
            self.state["position"] = "short"
            self.state["last_signal_at"] = now
            return {
                "action": "SELL",
                "symbol": snapshot["symbol"],
                "price": snapshot["mid_price"],
                "type": "MARKET",
                "metadata": metadata,
            }
        if abs(imbalance) <= self.config.exit_threshold and self.state["position"] != "flat":
            side = "SELL" if self.state["position"] == "long" else "BUY"
            self.state["position"] = "flat"
            self.state["last_signal_at"] = now
            return {
                "action": side,
                "symbol": snapshot["symbol"],
                "price": snapshot["mid_price"],
                "type": "MARKET",
                "metadata": metadata | {"exit": True},
            }

        return {"action": "HOLD"}

    def _in_cooldown(self, now: datetime) -> bool:
        last_signal: Optional[datetime] = self.state.get("last_signal_at")
        if not last_signal:
            return False
        return now - last_signal < timedelta(seconds=self.config.cooldown_seconds)

    def _latest_snapshot(self) -> Optional[Dict[str, Any]]:
        getter = getattr(self.data_feed, "get_latest_order_book", None)
        if not callable(getter):
            raise RuntimeError("Data feed does not expose order book snapshots.")
        snapshot = getter(self.config.symbol)
        if not snapshot:
            return None
        bids: List[Dict[str, float]] = snapshot.get("bids") or []
        asks: List[Dict[str, float]] = snapshot.get("asks") or []
        if not bids or not asks:
            return None

        buy_pressure = sum(level["size"] for level in bids[: self.config.depth])
        sell_pressure = sum(level["size"] for level in asks[: self.config.depth])
        total_pressure = buy_pressure + sell_pressure
        imbalance = (buy_pressure - sell_pressure) / total_pressure if total_pressure else 0.0
        best_bid = bids[0]["price"]
        best_ask = asks[0]["price"]
        mid_price = (best_bid + best_ask) / 2
        return {
            "symbol": snapshot.get("symbol", self.config.symbol),
            "timestamp": snapshot.get("timestamp", datetime.now(timezone.utc)),
            "imbalance": imbalance,
            "buy_pressure": buy_pressure,
            "sell_pressure": sell_pressure,
            "mid_price": mid_price,
        }


try:
    registry.register("order_book_imbalance", OrderBookImbalanceStrategy)
except ValueError:
    pass
