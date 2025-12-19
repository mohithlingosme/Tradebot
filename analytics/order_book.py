from __future__ import annotations

"""Order book analytics for imbalance-driven strategies."""

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Sequence


@dataclass
class Level:
    price: float
    size: float


@dataclass
class OrderBookSnapshotData:
    symbol: str
    timestamp: datetime
    bids: List[Level]
    asks: List[Level]

    @property
    def best_bid(self) -> float | None:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> float | None:
        return self.asks[0].price if self.asks else None


@dataclass
class ImbalancePoint:
    timestamp: datetime
    imbalance: float
    state: str


@dataclass
class OrderBookAnalysis:
    snapshot: OrderBookSnapshotData
    imbalance: float
    state: str
    buy_pressure: float
    sell_pressure: float
    spread: float
    history: List[ImbalancePoint]


class OrderBookImbalanceAnalyzer:
    """Compute liquidity imbalance and classify short-term microstructure regime."""

    def __init__(self, depth: int = 5, threshold: float = 0.15) -> None:
        self.depth = depth
        self.threshold = threshold

    def analyze(self, snapshots: Sequence[object]) -> OrderBookAnalysis:
        if not snapshots:
            raise ValueError("No order book snapshots available.")
        parsed = [self._to_snapshot(snapshot) for snapshot in snapshots]
        latest = parsed[-1]
        buy_pressure = self._aggregate_pressure(latest.bids)
        sell_pressure = self._aggregate_pressure(latest.asks)
        imbalance = self._imbalance(buy_pressure, sell_pressure)
        state = self._classify_state(imbalance)
        history = [
            ImbalancePoint(
                timestamp=snapshot.timestamp,
                imbalance=self._imbalance(
                    self._aggregate_pressure(snapshot.bids),
                    self._aggregate_pressure(snapshot.asks),
                ),
                state=self._classify_state(
                    self._imbalance(
                        self._aggregate_pressure(snapshot.bids),
                        self._aggregate_pressure(snapshot.asks),
                    )
                ),
            )
            for snapshot in parsed
        ]
        spread = (
            float(latest.best_ask - latest.best_bid)
            if latest.best_bid is not None and latest.best_ask is not None
            else 0.0
        )
        return OrderBookAnalysis(
            snapshot=latest,
            imbalance=imbalance,
            state=state,
            buy_pressure=buy_pressure,
            sell_pressure=sell_pressure,
            spread=spread,
            history=history[-100:],
        )

    def _aggregate_pressure(self, levels: List[Level]) -> float:
        relevant = levels[: self.depth]
        return float(sum(level.size for level in relevant))

    def _imbalance(self, buy_pressure: float, sell_pressure: float) -> float:
        denom = buy_pressure + sell_pressure
        if denom == 0:
            return 0.0
        return (buy_pressure - sell_pressure) / denom

    def _classify_state(self, imbalance: float) -> str:
        if imbalance >= self.threshold:
            return "bullish"
        if imbalance <= -self.threshold:
            return "bearish"
        return "balanced"

    def _to_snapshot(self, snapshot: object) -> OrderBookSnapshotData:
        if hasattr(snapshot, "bids") and hasattr(snapshot, "asks"):
            bids_raw = getattr(snapshot, "bids")
            asks_raw = getattr(snapshot, "asks")
            ts_value = getattr(snapshot, "ts_utc", getattr(snapshot, "timestamp", None))
            if hasattr(ts_value, "to_pydatetime"):
                timestamp = ts_value.to_pydatetime()
            else:
                timestamp = datetime.fromisoformat(ts_value) if isinstance(ts_value, str) else ts_value
            symbol = getattr(snapshot, "symbol", "UNKNOWN")
        elif isinstance(snapshot, dict):
            bids_raw = snapshot.get("bids", [])
            asks_raw = snapshot.get("asks", [])
            timestamp = snapshot.get("timestamp") or snapshot.get("ts_utc")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            symbol = snapshot.get("symbol", "UNKNOWN")
        else:
            raise ValueError("Unsupported snapshot format.")

        bids = [self._to_level(level) for level in bids_raw if level is not None]
        asks = [self._to_level(level) for level in asks_raw if level is not None]
        bids.sort(key=lambda level: level.price, reverse=True)
        asks.sort(key=lambda level: level.price)
        return OrderBookSnapshotData(symbol=symbol, timestamp=timestamp, bids=bids, asks=asks)

    def _to_level(self, level: object) -> Level:
        if isinstance(level, dict):
            price = float(level.get("price"))
            size = float(level.get("size", level.get("qty", 0)))
        elif isinstance(level, (list, tuple)):
            price = float(level[0])
            size = float(level[1])
        else:
            price = float(getattr(level, "price"))
            size = float(getattr(level, "size"))
        return Level(price=price, size=size)
