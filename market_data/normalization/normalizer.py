"""
Data normalizer that converts provider-shaped payloads into canonical Pydantic models.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import uuid4

from .models import Trade, Quote, Candle

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalizes provider-specific data into canonical models."""

    def __init__(self, provider_id: int, instrument_id: int):
        self.provider_id = provider_id
        self.instrument_id = instrument_id

    def normalize_trade(self, raw_trade: Dict) -> Optional[Trade]:
        """Normalize a single trade."""
        try:
            return Trade(
                provider_id=self.provider_id,
                instrument_id=self.instrument_id,
                trade_id=raw_trade.get("trade_id"),
                price=Decimal(str(raw_trade["price"])),
                size=Decimal(str(raw_trade["size"])),
                side=raw_trade.get("side", "unknown"),
                event_time=raw_trade["event_time"],
                received_at=datetime.utcnow(),
                ingest_id=uuid4()
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to normalize trade: {e}, data: {raw_trade}")
            return None

    def normalize_quote(self, raw_quote: Dict) -> Optional[Quote]:
        """Normalize a single quote."""
        try:
            return Quote(
                provider_id=self.provider_id,
                instrument_id=self.instrument_id,
                bid_price=Decimal(str(raw_quote["bid_price"])) if raw_quote.get("bid_price") else None,
                bid_size=Decimal(str(raw_quote["bid_size"])) if raw_quote.get("bid_size") else None,
                ask_price=Decimal(str(raw_quote["ask_price"])) if raw_quote.get("ask_price") else None,
                ask_size=Decimal(str(raw_quote["ask_size"])) if raw_quote.get("ask_size") else None,
                last_price=Decimal(str(raw_quote["last_price"])) if raw_quote.get("last_price") else None,
                last_size=Decimal(str(raw_quote["last_size"])) if raw_quote.get("last_size") else None,
                event_time=raw_quote["event_time"],
                received_at=datetime.utcnow(),
                ingest_id=uuid4()
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to normalize quote: {e}, data: {raw_quote}")
            return None

    def normalize_candle(self, raw_candle: Dict, granularity: str) -> Optional[Candle]:
        """Normalize a single candle."""
        try:
            return Candle(
                provider_id=self.provider_id,
                instrument_id=self.instrument_id,
                granularity=granularity,
                bucket_start=raw_candle["event_time"],  # Assuming event_time is bucket start
                open_price=Decimal(str(raw_candle["open"])),
                high_price=Decimal(str(raw_candle["high"])),
                low_price=Decimal(str(raw_candle["low"])),
                close_price=Decimal(str(raw_candle["close"])),
                volume=Decimal(str(raw_candle["volume"])),
                event_time=raw_candle["event_time"],
                received_at=datetime.utcnow(),
                ingest_id=uuid4()
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to normalize candle: {e}, data: {raw_candle}")
            return None

    def normalize_trades(self, raw_trades: List[Dict]) -> List[Trade]:
        """Normalize a list of trades."""
        normalized = []
        for raw_trade in raw_trades:
            trade = self.normalize_trade(raw_trade)
            if trade:
                normalized.append(trade)
        return normalized

    def normalize_quotes(self, raw_quotes: List[Dict]) -> List[Quote]:
        """Normalize a list of quotes."""
        normalized = []
        for raw_quote in raw_quotes:
            quote = self.normalize_quote(raw_quote)
            if quote:
                normalized.append(quote)
        return normalized

    def normalize_candles(self, raw_candles: List[Dict], granularity: str) -> List[Candle]:
        """Normalize a list of candles."""
        normalized = []
        for raw_candle in raw_candles:
            candle = self.normalize_candle(raw_candle, granularity)
            if candle:
                normalized.append(candle)
        return normalized
