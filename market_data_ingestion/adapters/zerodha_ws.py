from __future__ import annotations

"""Zerodha-style WebSocket adapter with reconnect/backoff support."""

import asyncio
import contextlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

import tenacity
import websockets

from market_data_ingestion.adapters.base import BaseMarketDataAdapter, NormalizedTick
from market_data_ingestion.src.logging_config import get_logger

logger = get_logger(__name__)


class ZerodhaWebSocketAdapter(BaseMarketDataAdapter):
    """Lightweight client for Zerodha-like quote streams."""

    provider = "zerodha"

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._api_key = config.get("api_key", "")
        self._access_token = config.get("access_token", "")
        self._feed_url = config.get("websocket_url", "wss://ws.zerodha.mock")
        self._reconnect_max = int(config.get("max_reconnect_interval", 30))
        self._symbols: List[str] = []
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._consumer_task: Optional[asyncio.Task[None]] = None
        self._queue: asyncio.Queue[NormalizedTick] = asyncio.Queue()
        self._stop_event = asyncio.Event()

    async def connect(self) -> None:
        """Start the streaming loop."""
        if self._consumer_task:
            return
        self._stop_event.clear()
        self._consumer_task = asyncio.create_task(self._run_forever())

    async def close(self) -> None:
        """Stop streaming and close websocket."""
        self._stop_event.set()
        if self._consumer_task:
            self._consumer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._consumer_task
            self._consumer_task = None
        if self._ws:
            await self._ws.close()
            self._ws = None
        await self._mark_connected(False)

    async def subscribe(self, symbols: List[str]) -> None:
        self._symbols = symbols
        if self._ws:
            frame = {"action": "subscribe", "tokens": symbols}
            await self._ws.send(json.dumps(frame))

    async def stream(self) -> AsyncGenerator[NormalizedTick, None]:
        """Yield ticks from the internal queue."""
        await self.connect()
        while True:
            tick = await self._queue.get()
            yield tick

    async def _run_forever(self) -> None:
        attempt = 0
        while not self._stop_event.is_set():
            try:
                await self._connect_once()
                attempt = 0  # reset after successful session
            except asyncio.CancelledError:
                break
            except Exception as exc:
                attempt += 1
                delay = min(self._reconnect_max, 2 ** attempt)
                logger.warning("Zerodha WS disconnected (%s). Reconnecting in %ss", exc, delay)
                await asyncio.sleep(delay)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(5),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _handshake(self, ws: websockets.WebSocketClientProtocol) -> None:
        auth_frame = {
            "action": "authenticate",
            "api_key": self._api_key,
            "access_token": self._access_token,
        }
        await ws.send(json.dumps(auth_frame))
        response = json.loads(await ws.recv())
        if response.get("status") != "ok":
            raise RuntimeError(f"Authentication failed: {response}")
        if self._symbols:
            await ws.send(json.dumps({"action": "subscribe", "tokens": self._symbols}))

    async def _connect_once(self) -> None:
        async with websockets.connect(
            self._feed_url,
            ping_interval=None,
            max_queue=None,
            close_timeout=5,
        ) as ws:
            self._ws = ws
            await self._mark_connected(True)
            await self._handshake(ws)
            logger.info("Connected to Zerodha feed at %s", self._feed_url)
            heartbeat = asyncio.create_task(self._heartbeat(ws))
            try:
                async for message in ws:
                    tick = self._process_message(message)
                    if tick:
                        await self._queue.put(tick)
            finally:
                heartbeat.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await heartbeat
                await self._mark_connected(False)

    async def _heartbeat(self, ws: websockets.WebSocketClientProtocol) -> None:
        interval = int(self.config.get("heartbeat_interval", 20))
        while True:
            await asyncio.sleep(interval)
            try:
                await ws.ping()
            except Exception as exc:
                logger.warning("Heartbeat failed: %s", exc)
                break

    def _process_message(self, raw_message: str) -> Optional[NormalizedTick]:
        try:
            payload = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.debug("Ignoring non-JSON frame: %s", raw_message)
            return None
        if payload.get("type") == "heartbeat":
            return None
        try:
            return self._normalize(payload)
        except Exception as exc:
            logger.error("Failed to normalize tick %s (%s)", payload, exc)
            return None

    def _normalize(self, payload: Dict[str, Any]) -> NormalizedTick:
        symbol = str(payload.get("instrument_token") or payload.get("symbol") or "UNKNOWN")
        timestamp = payload.get("timestamp") or payload.get("last_trade_time")
        ts = self._parse_timestamp(timestamp)
        price = self._normalize_price(payload.get("last_price"))
        volume = float(payload.get("volume") or payload.get("last_quantity") or 0.0)
        return NormalizedTick(
            symbol=symbol,
            ts_utc=ts,
            price=price,
            volume=volume,
            provider=self.provider,
            raw=payload,
        )

    @staticmethod
    def _parse_timestamp(raw_ts: Any) -> datetime:
        if isinstance(raw_ts, (int, float)):
            return datetime.fromtimestamp(raw_ts, tz=timezone.utc)
        if isinstance(raw_ts, str):
            try:
                return datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)
