from .base import BaseMarketDataAdapter, NormalizedTick
from .alphavantage import AlphaVantageAdapter
from .yfinance import YFinanceAdapter
from .kite_ws import KiteWebSocketAdapter
from .fyers import FyersAdapter
from .binance import BinanceAdapter
from .polygon import PolygonAdapter


ADAPTER_REGISTRY = {
    "alphavantage": AlphaVantageAdapter,
    "yfinance": YFinanceAdapter,
    "kite": KiteWebSocketAdapter,
    "fyers": FyersAdapter,
    "binance": BinanceAdapter,
    "polygon": PolygonAdapter,
}


def get_adapter(name: str, config):
    cls = ADAPTER_REGISTRY.get(name.lower())
    if not cls:
        raise ValueError(f"Adapter '{name}' not found")
    return cls(config)
