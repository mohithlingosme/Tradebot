import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional, Tuple

import websockets

from data_engine import Candle, CSVLogger, LiveDataEngine

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Tick:
    """
    Represents a single market tick (price update).
    """
    symbol: str
    price: float
    volume: float
    timestamp: datetime

@dataclass
class Candle:
    """
    Represents an OHLC candle for a given timeframe.
    """
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime

class DataFeed:
    """
    Handles real-time market data ingestion via WebSocket.
    """
    def __init__(
        self,
        url: str,
        symbols: List[str],
        on_tick: Optional[Callable[[Tick], None]] = None,
        live_engine: Optional[LiveDataEngine] = None,
    ):
        self.url = url
        self.symbols = symbols
        self.on_tick = on_tick
        self.live_engine = live_engine
        self.running = False
        self.ws = None
        self.reconnect_delay = 5  # Seconds

    async def start(self):
        """
        Starts the WebSocket connection loop with auto-reconnect.
        """
        self.running = True
        while self.running:
            try:
                logger.info(f"Connecting to {self.url}...")
                async with websockets.connect(self.url) as ws:
                    self.ws = ws
                    logger.info("Connected.")
                    await self._subscribe()
                    await self._listen()
            except (websockets.ConnectionClosed, OSError) as e:
                logger.error(f"Connection lost: {e}. Reconnecting in {self.reconnect_delay}s...")
                await asyncio.sleep(self.reconnect_delay)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(self.reconnect_delay)

    async def stop(self):
        """
        Stops the data feed.
        """
        self.running = False
        if self.ws:
            await self.ws.close()

    async def _subscribe(self):
        """
        Sends subscription message for the requested symbols.
        Implementation depends on the specific exchange API.
        """
        # Example subscription payload (generic)
        payload = {
            "method": "SUBSCRIBE",
            "params": [f"{s.lower()}@trade" for s in self.symbols],
            "id": 1
        }
        await self.ws.send(json.dumps(payload))
        logger.info(f"Subscribed to {self.symbols}")

    async def _listen(self):
        """
        Listens for incoming messages.
        """
        async for message in self.ws:
            if not self.running:
                break
            await self._handle_message(message)

    async def _handle_message(self, message: str):
        """
        Parses the incoming message and converts it to a Tick object.
        """
        try:
            data = json.loads(message)

            # Example parsing logic (assuming a generic structure similar to Binance)
            # This needs to be adapted to the specific WebSocket API being used.
            if 'e' in data and data['e'] == 'trade':
                tick = Tick(
                    symbol=data['s'],
                    price=float(data['p']),
                    volume=float(data['q']),
                    timestamp=datetime.fromtimestamp(data['T'] / 1000)
                )

                if self.on_tick:
                    self.on_tick(tick)

                if self.live_engine:
                    current, completed = self.live_engine.on_tick(
                        tick.symbol, tick.timestamp, tick.price, tick.volume
                    )
                    if completed:
                        logger.debug("Completed candle %s", completed.to_dict())
                    logger.debug("Current candle %s", current.to_dict())

                logger.debug(f"Tick received: {tick}")

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON message")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

class CandleAggregator:
    """
    Compatibility wrapper that builds candles using LiveDataEngine.
    """

    def __init__(
        self,
        on_candle: Optional[Callable[[Candle], None]] = None,
        timeframe_s: int = 60,
        window_size: int = 120,
        logger: Optional[CSVLogger] = None,
    ) -> None:
        self.engine = LiveDataEngine(
            timeframe_s=timeframe_s,
            window_size=window_size,
            logger=logger,
            on_candle=on_candle,
        )

    def add_tick(self, tick: Tick) -> Tuple[Candle, Optional[Candle]]:
        """
        Add a tick and return the current candle plus a completed candle (if any).
        """
        return self.engine.on_tick(tick.symbol, tick.timestamp, tick.price, tick.volume)

