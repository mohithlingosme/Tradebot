"""
Unit tests for data normalizer.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID

from market_data.normalization.normalizer import DataNormalizer


class TestDataNormalizer:
    """Test DataNormalizer functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.normalizer = DataNormalizer(provider_id=1, instrument_id=1)

    def test_normalize_trade_success(self):
        """Test successful trade normalization."""
        raw_trade = {
            "trade_id": "12345",
            "price": 150.50,
            "size": 100.0,
            "side": "buy",
            "event_time": datetime(2024, 1, 1, 12, 0, 0),
            "symbol": "AAPL"
        }

        trade = self.normalizer.normalize_trade(raw_trade)

        assert trade is not None
        assert trade.provider_id == 1
        assert trade.instrument_id == 1
        assert trade.trade_id == "12345"
        assert trade.price == Decimal("150.50")
        assert trade.size == Decimal("100")
        assert trade.side == "buy"
        assert isinstance(trade.ingest_id, UUID)

    def test_normalize_trade_missing_required_fields(self):
        """Test trade normalization with missing required fields."""
        # Missing price
        raw_trade = {
            "trade_id": "12345",
            "size": 100.0,
            "side": "buy",
            "event_time": datetime(2024, 1, 1, 12, 0, 0)
        }

        trade = self.normalizer.normalize_trade(raw_trade)
        assert trade is None

    def test_normalize_trade_invalid_data(self):
        """Test trade normalization with invalid data types."""
        raw_trade = {
            "trade_id": "12345",
            "price": "invalid_price",
            "size": 100.0,
            "side": "buy",
            "event_time": datetime(2024, 1, 1, 12, 0, 0)
        }

        with pytest.raises(Exception):
            self.normalizer.normalize_trade(raw_trade)

    def test_normalize_quote_success(self):
        """Test successful quote normalization."""
        raw_quote = {
            "bid_price": 150.00,
            "bid_size": 100.0,
            "ask_price": 150.50,
            "ask_size": 200.0,
            "event_time": datetime(2024, 1, 1, 12, 0, 0),
            "symbol": "AAPL"
        }

        quote = self.normalizer.normalize_quote(raw_quote)

        assert quote is not None
        assert quote.provider_id == 1
        assert quote.instrument_id == 1
        assert quote.bid_price == Decimal("150.00")
        assert quote.ask_price == Decimal("150.50")
        assert isinstance(quote.ingest_id, UUID)

    def test_normalize_quote_with_none_values(self):
        """Test quote normalization with None values."""
        raw_quote = {
            "bid_price": None,
            "bid_size": None,
            "ask_price": 150.50,
            "ask_size": 200.0,
            "event_time": datetime(2024, 1, 1, 12, 0, 0)
        }

        quote = self.normalizer.normalize_quote(raw_quote)

        assert quote is not None
        assert quote.bid_price is None
        assert quote.bid_size is None
        assert quote.ask_price == Decimal("150.50")

    def test_normalize_candle_success(self):
        """Test successful candle normalization."""
        raw_candle = {
            "open": 150.00,
            "high": 151.00,
            "low": 149.50,
            "close": 150.75,
            "volume": 1000.0,
            "event_time": datetime(2024, 1, 1, 12, 0, 0),
            "symbol": "AAPL",
            "interval": "1m"
        }

        candle = self.normalizer.normalize_candle(raw_candle, "1m")

        assert candle is not None
        assert candle.provider_id == 1
        assert candle.instrument_id == 1
        assert candle.granularity == "1m"
        assert candle.open_price == Decimal("150.00")
        assert candle.high_price == Decimal("151.00")
        assert candle.low_price == Decimal("149.50")
        assert candle.close_price == Decimal("150.75")
        assert candle.volume == Decimal("1000")

    def test_normalize_trades_batch(self):
        """Test batch trade normalization."""
        raw_trades = [
            {
                "trade_id": "12345",
                "price": 150.50,
                "size": 100.0,
                "side": "buy",
                "event_time": datetime(2024, 1, 1, 12, 0, 0)
            },
            {
                "trade_id": "12346",
                "price": 150.75,
                "size": 50.0,
                "side": "sell",
                "event_time": datetime(2024, 1, 1, 12, 0, 1)
            }
        ]

        trades = self.normalizer.normalize_trades(raw_trades)

        assert len(trades) == 2
        assert trades[0].trade_id == "12345"
        assert trades[1].trade_id == "12346"

    def test_normalize_quotes_batch(self):
        """Test batch quote normalization."""
        raw_quotes = [
            {
                "bid_price": 150.00,
                "ask_price": 150.50,
                "event_time": datetime(2024, 1, 1, 12, 0, 0)
            },
            {
                "bid_price": 150.25,
                "ask_price": 150.75,
                "event_time": datetime(2024, 1, 1, 12, 0, 1)
            }
        ]

        quotes = self.normalizer.normalize_quotes(raw_quotes)

        assert len(quotes) == 2
        assert quotes[0].bid_price == Decimal("150.00")
        assert quotes[1].bid_price == Decimal("150.25")

    def test_normalize_candles_batch(self):
        """Test batch candle normalization."""
        raw_candles = [
            {
                "open": 150.00,
                "high": 151.00,
                "low": 149.50,
                "close": 150.75,
                "volume": 1000.0,
                "event_time": datetime(2024, 1, 1, 12, 0, 0)
            }
        ]

        candles = self.normalizer.normalize_candles(raw_candles, "1m")

        assert len(candles) == 1
        assert candles[0].granularity == "1m"
        assert candles[0].open_price == Decimal("150.00")
