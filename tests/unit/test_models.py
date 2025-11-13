import pytest
from typing import Dict, Any

# Define a sample candle for testing
SAMPLE_CANDLE: Dict[str, Any] = {
    "symbol": "TEST.STK",
    "ts_utc": "2024-01-01T00:00:00Z",
    "open": 150.00,
    "high": 150.75,
    "low": 149.50,
    "close": 150.25,
    "volume": 1000,
    "provider": "test_provider",
    "meta": {}
}

def test_candle_creation():
    """Test the creation of a candle dictionary."""
    assert SAMPLE_CANDLE["symbol"] == "TEST.STK"
    assert SAMPLE_CANDLE["open"] == 150.00
    assert SAMPLE_CANDLE["high"] == 150.75
    assert SAMPLE_CANDLE["low"] == 149.50
    assert SAMPLE_CANDLE["close"] == 150.25
    assert SAMPLE_CANDLE["volume"] == 1000
    assert SAMPLE_CANDLE["provider"] == "test_provider"

def test_candle_values_are_numeric():
    """Test that candle values are of numeric types."""
    assert isinstance(SAMPLE_CANDLE["open"], float)
    assert isinstance(SAMPLE_CANDLE["high"], float)
    assert isinstance(SAMPLE_CANDLE["low"], float)
    assert isinstance(SAMPLE_CANDLE["close"], float)
    assert isinstance(SAMPLE_CANDLE["volume"], int)

def test_candle_symbol_is_string():
    """Test that the candle symbol is a string."""
    assert isinstance(SAMPLE_CANDLE["symbol"], str)

def test_candle_provider_is_string():
    """Test that the candle provider is a string."""
    assert isinstance(SAMPLE_CANDLE["provider"], str)

def test_candle_meta_is_dict():
    """Test that the candle meta is a dictionary."""
    assert isinstance(SAMPLE_CANDLE["meta"], dict)
