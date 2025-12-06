import asyncio
import os
import tempfile
from pathlib import Path
from typing import Generator

import httpx
import pytest
from _pytest.fixtures import FixtureDef
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_HTTPX_CLIENT_INIT = httpx.Client.__init__


def _compatible_httpx_client_init(self, *args, **kwargs):
    """Allow Starlette's TestClient to run with httpx >=0.28."""
    kwargs.pop("app", None)
    return _HTTPX_CLIENT_INIT(self, *args, **kwargs)


httpx.Client.__init__ = _compatible_httpx_client_init


@pytest.fixture(autouse=True)
def ensure_fixturedef_unittest_attribute():
    """Ensure pytest_asyncio can reference FixtureDef.unittest without import errors."""
    if not hasattr(FixtureDef, "unittest"):
        setattr(FixtureDef, "unittest", False)
    yield


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Return a test settings object preconfigured for safe in-memory dev mode."""
    from backend.config.settings import Settings

    # Override settings for testing
    test_env = {
        "FINBOT_MODE": "dev",
        "DATABASE_URL": "sqlite:///:memory:",
        "APP_ENV": "test",
        "LIVE_TRADING_CONFIRM": "false",
        "LOG_LEVEL": "WARNING",
    }

    # Monkeypatch environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    settings = Settings()

    # Restore original env after fixture
    yield settings

    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def fake_market_data():
    """Yield synthetic OHLC data for a few symbols."""
    import pandas as pd
    from datetime import datetime, timedelta

    # Generate sample data
    symbols = ["AAPL", "GOOGL", "MSFT"]
    data = []
    base_time = datetime(2023, 1, 1, 9, 15)

    for symbol in symbols:
        for i in range(100):  # 100 bars
            timestamp = base_time + timedelta(minutes=i * 5)
            open_price = 100 + i * 0.1
            high_price = open_price + 1
            low_price = open_price - 1
            close_price = open_price + (0.5 if i % 2 == 0 else -0.5)
            volume = 1000 + i * 10

            data.append({
                "timestamp": timestamp,
                "symbol": symbol,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            })

    df = pd.DataFrame(data)
    yield df


@pytest.fixture(scope="function")
def test_db():
    """Provide an in-memory SQLite database for tests."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables (assuming models are imported)
    from database.schemas import Base  # Adjust import as needed
    Base.metadata.create_all(bind=engine)

    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Yield session
    session = SessionLocal()
    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def api_client(test_settings):
    """Return a FastAPI test client bound to the backend app."""
    from fastapi.testclient import TestClient
    from backend.api.main import app

    # Override settings in app
    app.state.settings = test_settings

    client = TestClient(app)
    yield client
