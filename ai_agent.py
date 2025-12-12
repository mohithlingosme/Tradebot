"""Autonomous trading agent that watches Alpaca crypto markets and records actions.

The previous implementation frequently crashed because environment variables were
missing, API/base URLs were malformed, or database connections were left open.
This rewrite adds strict environment validation, resilient API handling, and a
clean SQLAlchemy session scope so that failures surface clearly instead of
tearing down the agent loop.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from collections import deque
from contextlib import contextmanager
from importlib import import_module
from typing import Deque, Optional

from dotenv import load_dotenv

try:
    from alpaca_trade_api.rest import REST, APIError
except ImportError as exc:  # pragma: no cover - missing dependency is fatal
    raise RuntimeError(
        "The 'alpaca_trade_api' package is required. Install it with "
        "'pip install alpaca-trade-api'."
    ) from exc

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# --------------------------------------------------------------------------- #
# Environment & logging setup
# --------------------------------------------------------------------------- #
load_dotenv()
logging.basicConfig(
    level=os.getenv("AI_AGENT_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("ai_agent")


def require_env(name: str, default: Optional[str] = None) -> str:
    """Fetch a required environment variable or exit with a helpful error."""
    value = os.getenv(name, default)
    if value:
        return value
    logger.error("Missing required environment variable: %s", name)
    raise SystemExit(1)


def normalize_alpaca_base_url(url: str) -> str:
    """Ensure the Alpaca base URL does not include the API version suffix."""
    normalized = url.rstrip("/")
    if normalized.endswith("/v2"):
        normalized = normalized[:-3]
    return normalized


def resolve_trade_model():
    """Load the Trade ORM class from any of the known modules."""
    for module_path in ("models", "backend.api.main", "main"):
        try:
            module = import_module(module_path)
            trade_cls = getattr(module, "Trade")
            logger.debug("Loaded Trade model from %s", module_path)
            return trade_cls
        except (ImportError, AttributeError):
            continue
    raise RuntimeError("Unable to import Trade model; checked models, backend.api.main, main.")


Trade = resolve_trade_model()

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
ALPACA_API_KEY = require_env("ALPACA_API_KEY")
ALPACA_SECRET_KEY = require_env("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = normalize_alpaca_base_url(require_env("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"))
DATABASE_URL = require_env("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finbot_db")

SYMBOL = os.getenv("AI_AGENT_SYMBOL", "BTC/USD").upper()
TRADE_QUANTITY = float(os.getenv("AI_AGENT_QUANTITY", "0.0001"))
SLEEP_SECONDS = int(os.getenv("AI_AGENT_SLEEP_TIME", "10"))
WINDOW_SIZE = int(os.getenv("AI_AGENT_WINDOW", "5"))
BUY_THRESHOLD = float(os.getenv("AI_AGENT_BUY_THRESHOLD", "0.9999"))
SELL_THRESHOLD = float(os.getenv("AI_AGENT_SELL_THRESHOLD", "1.0001"))
CRYPTO_EXCHANGE = os.getenv("AI_AGENT_EXCHANGE", "CBSE")

# --------------------------------------------------------------------------- #
# External clients
# --------------------------------------------------------------------------- #
try:
    alpaca_client = REST(
        key_id=ALPACA_API_KEY,
        secret_key=ALPACA_SECRET_KEY,
        base_url=ALPACA_BASE_URL,
        api_version="v2",
    )
except Exception as exc:  # pragma: no cover - network errors happen at runtime
    logger.error("Failed to initialize Alpaca client: %s", exc)
    raise

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def log_trade(symbol: str, side: str, qty: float, price: float) -> None:
    """Persist the trade so the Finbot UI can display agent activity."""
    try:
        with session_scope() as db:
            trade = Trade(
                symbol=symbol,
                side=side,
                quantity=float(qty),
                price=float(price),
                status="AI_FILLED",
            )
            db.add(trade)
    except Exception:
        logger.exception("Failed to log trade to the database.")
    else:
        logger.info("🤖 AI AGENT: %s %s @ $%.2f", side.upper(), symbol, price)


# --------------------------------------------------------------------------- #
# Strategy primitives
# --------------------------------------------------------------------------- #
class PriceWindow:
    """Rolling window helper that tracks the most recent close prices."""

    def __init__(self, size: int):
        if size < 2:
            raise ValueError("Price window size must be at least 2.")
        self._values: Deque[float] = deque(maxlen=size)

    def __len__(self) -> int:
        return len(self._values)

    @property
    def max_size(self) -> int:
        return self._values.maxlen or 0

    def add(self, price: float) -> None:
        self._values.append(float(price))

    def full(self) -> bool:
        return len(self._values) == self.max_size

    def average(self) -> Optional[float]:
        if not self._values:
            return None
        return sum(self._values) / len(self._values)

    def clear(self) -> None:
        self._values.clear()


class TradingAgent:
    """Simple mean-reversion agent that polls Alpaca and executes trades."""

    def __init__(
        self,
        client: REST,
        symbol: str,
        quantity: float,
        exchange: str,
        window_size: int,
        buy_threshold: float,
        sell_threshold: float,
        sleep_seconds: int,
    ):
        self.client = client
        self.symbol = symbol.upper()
        self.quantity = quantity
        self.exchange = exchange
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.sleep_seconds = sleep_seconds
        self.price_window = PriceWindow(window_size)

    def fetch_price(self) -> Optional[float]:
        try:
            bars = self.client.get_latest_crypto_bars([self.symbol], exchange=self.exchange)
        except APIError as exc:
            logger.error("Failed to fetch bars for %s: %s", self.symbol, exc)
            return None
        except Exception:
            logger.exception("Unexpected error while fetching bars.")
            return None

        bar = None
        if isinstance(bars, dict):
            bar = bars.get(self.symbol)
        else:
            try:
                bar = bars[self.symbol]
            except Exception:
                bar = None

        if bar is None:
            logger.warning("No crypto bar returned for %s.", self.symbol)
            return None

        if isinstance(bar, list):
            bar = bar[0] if bar else None
        if bar is None:
            logger.warning("Empty bar list returned for %s.", self.symbol)
            return None

        price = getattr(bar, "c", None) or getattr(bar, "close", None)
        if price is None:
            logger.warning("Bar data missing close price for %s: %s", self.symbol, bar)
            return None
        return float(price)

    def execute_trade(self, side: str, price: float) -> None:
        try:
            order = self.client.submit_order(
                symbol=self.symbol,
                qty=self.quantity,
                side=side,
                type="market",
                time_in_force="gtc",
            )
        except APIError as exc:
            logger.error("Order failed (%s %s): %s", side, self.symbol, exc)
            return
        except Exception:
            logger.exception("Unexpected order failure for %s.", self.symbol)
            return

        log_trade(self.symbol, side, self.quantity, price)
        logger.info("Order submitted successfully. Alpaca id=%s", getattr(order, "id", "unknown"))
        self.price_window.clear()

    def step(self) -> None:
        price = self.fetch_price()
        if price is None:
            return

        self.price_window.add(price)
        if not self.price_window.full():
            logger.info(
                "👀 Gathering data... %s/%s (Price: %.2f)",
                len(self.price_window),
                self.price_window.max_size,
                price,
            )
            return

        average_price = self.price_window.average()
        if average_price is None:
            return

        logger.info("💰 Price: %.4f | 📊 Avg: %.4f", price, average_price)

        if price <= average_price * self.buy_threshold:
            logger.info("📉 Dip detected! Submitting BUY order.")
            self.execute_trade("buy", price)
        elif price >= average_price * self.sell_threshold:
            logger.info("📈 Spike detected! Submitting SELL order.")
            self.execute_trade("sell", price)
        else:
            logger.info("😴 Market is calm. Holding position.")

    def run(self) -> None:
        logger.info("🚀 AI Agent launched! Tracking %s ...", self.symbol)
        while True:
            try:
                self.step()
            except Exception:
                logger.exception("Unhandled error inside main loop.")
            time.sleep(self.sleep_seconds)


def main() -> None:
    if TRADE_QUANTITY <= 0:
        logger.error("AI_AGENT_QUANTITY must be positive.")
        sys.exit(1)

    agent = TradingAgent(
        client=alpaca_client,
        symbol=SYMBOL,
        quantity=TRADE_QUANTITY,
        exchange=CRYPTO_EXCHANGE,
        window_size=WINDOW_SIZE,
        buy_threshold=BUY_THRESHOLD,
        sell_threshold=SELL_THRESHOLD,
        sleep_seconds=SLEEP_SECONDS,
    )
    agent.run()


if __name__ == "__main__":
    main()
