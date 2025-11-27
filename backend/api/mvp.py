from __future__ import annotations

import asyncio
import itertools
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Set
import contextlib


Symbol = Literal["NIFTY", "BANKNIFTY"]
Side = Literal["BUY", "SELL"]


@dataclass
class Candle:
    symbol: Symbol
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class Signal:
    symbol: Symbol
    side: Side
    size: float


@dataclass
class Position:
    symbol: Symbol
    qty: float
    avg_price: float
    current_price: float

    @property
    def pnl(self) -> float:
        return (self.current_price - self.avg_price) * self.qty


@dataclass
class Order:
    id: str
    symbol: Symbol
    side: Side
    qty: float
    price: float
    status: str
    timestamp: float


class EmaCrossoverStrategy:
    def __init__(self, fast: int = 9, slow: int = 21):
        self.fast = fast
        self.slow = slow
        self.state: Dict[Symbol, Dict[str, float]] = {}

    def _ema(self, prev: float, price: float, period: int) -> float:
        k = 2 / (period + 1)
        return price * k + prev * (1 - k)

    def on_candle(self, candle: Candle) -> Optional[Signal]:
        s = self.state.setdefault(
            candle.symbol,
            {"fast": candle.close, "slow": candle.close, "last_cross": "FLAT"},
        )
        s["fast"] = self._ema(s["fast"], candle.close, self.fast)
        s["slow"] = self._ema(s["slow"], candle.close, self.slow)

        crossed_up = s["fast"] > s["slow"] and s["last_cross"] != "UP"
        crossed_down = s["fast"] < s["slow"] and s["last_cross"] != "DOWN"

        if crossed_up:
            s["last_cross"] = "UP"
            return Signal(symbol=candle.symbol, side="BUY", size=1)
        if crossed_down:
            s["last_cross"] = "DOWN"
            return Signal(symbol=candle.symbol, side="SELL", size=1)
        return None


class RiskManager:
    def __init__(self, max_daily_loss: float, max_position: float, max_positions: int):
        self.max_daily_loss = max_daily_loss
        self.max_position = max_position
        self.max_positions = max_positions

    def validate(self, signal: Signal, positions: Dict[Symbol, Position], realized_pnl: float) -> bool:
        # Allow flattening even if limits breached
        if signal.side == "SELL" and positions.get(signal.symbol, Position(signal.symbol, 0, 0, 0)).qty > 0:
            return True

        if realized_pnl <= -abs(self.max_daily_loss):
            return False

        symbol_pos = positions.get(signal.symbol)
        if symbol_pos and abs(symbol_pos.qty) >= self.max_position:
            return False

        if len([p for p in positions.values() if abs(p.qty) > 0]) >= self.max_positions:
            return False

        return True


class MockBroker:
    def __init__(self):
        self.positions: Dict[Symbol, Position] = {}
        self.orders: List[Order] = []
        self.realized_pnl: float = 0.0
        self.order_counter = itertools.count(1)

    def _lot_size(self, symbol: Symbol) -> float:
        return 50.0 if symbol == "NIFTY" else 25.0

    def place_order(self, signal: Signal, price: float) -> Order:
        qty = signal.size * self._lot_size(signal.symbol)
        oid = f"ORD-{next(self.order_counter)}"
        ts = time.time()
        order = Order(
            id=oid,
            symbol=signal.symbol,
            side=signal.side,
            qty=qty,
            price=price,
            status="FILLED",
            timestamp=ts,
        )
        self.orders.insert(0, order)
        self._apply_fill(order)
        return order

    def _apply_fill(self, order: Order) -> None:
        pos = self.positions.get(order.symbol)
        if not pos:
            if order.side == "BUY":
                self.positions[order.symbol] = Position(order.symbol, order.qty, order.price, order.price)
            return

        if order.side == "BUY":
            new_qty = pos.qty + order.qty
            pos.avg_price = (pos.avg_price * pos.qty + order.price * order.qty) / new_qty
            pos.qty = new_qty
            pos.current_price = order.price
        elif order.side == "SELL":
            # Realized PnL on closing qty up to existing position
            close_qty = min(pos.qty, order.qty)
            self.realized_pnl += (order.price - pos.avg_price) * close_qty
            pos.qty -= close_qty
            pos.current_price = order.price
            if pos.qty <= 0:
                pos.qty = 0
                pos.avg_price = 0

    def mark(self, symbol: Symbol, price: float) -> None:
        pos = self.positions.get(symbol)
        if pos:
            pos.current_price = price

    def get_positions(self) -> List[Dict[str, Any]]:
        return [
            {
                "symbol": p.symbol,
                "quantity": p.qty,
                "avg_price": p.avg_price,
                "current_price": p.current_price,
                "pnl": p.pnl,
            }
            for p in self.positions.values()
            if p.qty != 0
        ]

    def get_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [
            {
                "id": o.id,
                "symbol": o.symbol,
                "side": o.side,
                "qty": o.qty,
                "price": o.price,
                "status": o.status,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(o.timestamp)),
            }
            for o in self.orders[:limit]
        ]

    def portfolio_summary(self) -> Dict[str, Any]:
        unrealized = sum(p.pnl for p in self.positions.values())
        positions_value = sum(p.current_price * p.qty for p in self.positions.values())
        return {
            "pnl": self.realized_pnl + unrealized,
            "cash": 0,
            "positions_value": positions_value,
            "total_value": positions_value,
            "positions": self.get_positions(),
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": unrealized,
        }


class SubscriberHub:
    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        self.subscribers.discard(q)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        for q in list(self.subscribers):
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                pass


class MvpEngine:
    def __init__(self):
        self.running = False
        self.strategy = EmaCrossoverStrategy()
        self.risk = RiskManager(
            max_daily_loss=float(os.getenv("MVP_MAX_DAILY_LOSS", "10000")),
            max_position=float(os.getenv("MVP_MAX_POSITION_SIZE", "200")),
            max_positions=int(os.getenv("MVP_MAX_POSITIONS", "2")),
        )
        self.broker = MockBroker()
        self.last_prices: Dict[Symbol, float] = {"NIFTY": 20000.0, "BANKNIFTY": 45000.0}
        self.logs: List[Dict[str, Any]] = []
        self.state = "STOPPED"
        self.mode = "PAPER"
        self._task: Optional[asyncio.Task] = None
        self._hub = SubscriberHub()

    def log(self, level: str, message: str) -> None:
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "level": level.upper(),
            "message": message,
            "component": "mvp_loop",
        }
        self.logs.insert(0, entry)
        self.logs = self.logs[:200]

    async def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.state = "RUNNING"
        self._task = asyncio.create_task(self._run())
        self.log("INFO", "MVP trading loop started (PAPER)")

    async def stop(self) -> None:
        self.running = False
        self.state = "STOPPED"
        if self._task:
            self._task.cancel()
            with contextlib.suppress(Exception):
                await self._task
        self.log("INFO", "MVP trading loop stopped")

    async def _run(self) -> None:
        try:
            async for candle in self._ingestion():
                self.last_prices[candle.symbol] = candle.close
                self.broker.mark(candle.symbol, candle.close)

                signal = self.strategy.on_candle(candle)
                if signal:
                    if self.risk.validate(signal, self.broker.positions, self.broker.realized_pnl):
                        order = self.broker.place_order(signal, candle.close)
                        self.log("INFO", f"Order filled {order.id} {order.side} {order.symbol} @ {order.price}")
                    else:
                        self.log("WARN", f"Risk rejected {signal.side} on {signal.symbol}")

                snapshot = self.snapshot()
                await self._hub.broadcast({"type": "snapshot", **snapshot})
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            self.state = "ERROR"
            self.log("ERROR", f"Loop error: {exc}")

    async def _ingestion(self):
        symbols: List[Symbol] = ["NIFTY", "BANKNIFTY"]
        base = self.last_prices.copy()
        while self.running:
            for sym in symbols:
                drift = random.uniform(-30, 30)
                last = base[sym]
                open_ = last
                close = max(1.0, last + drift)
                high = max(open_, close) + random.uniform(0, 10)
                low = min(open_, close) - random.uniform(0, 10)
                volume = random.uniform(1_000, 10_000)
                base[sym] = close
                yield Candle(
                    symbol=sym,
                    timestamp=time.time(),
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                )
            await asyncio.sleep(1.0)

    def snapshot(self) -> Dict[str, Any]:
        portfolio = self.broker.portfolio_summary()
        return {
            "pnl": {
                "total": portfolio["pnl"],
                "realized": portfolio["realized_pnl"],
                "unrealized": portfolio["unrealized_pnl"],
            },
            "positions": self.broker.get_positions(),
            "orders": self.broker.get_orders(),
            "logs": self.logs,
            "strategy": {"name": "EMA Crossover", "state": self.state},
            "risk": {
                "max_daily_loss_pct": 0,
                "used_pct": 0,
                "circuit_breaker": False,
            },
            "mode": self.mode,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    async def subscribe(self) -> asyncio.Queue:
        return await self._hub.subscribe()

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        await self._hub.unsubscribe(q)


mvp_engine = MvpEngine()
