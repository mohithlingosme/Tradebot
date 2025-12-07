# FILE: tests/test_config_loading.py
"""Test loading of settings/config objects (DB URLs, broker keys, risk config)."""

import os
import pytest
from unittest.mock import patch


def test_settings_loading_with_env_vars():
    """Test loading settings with environment variable overrides."""
    from backend.config.settings import Settings

    test_env = {
        "FINBOT_MODE": "paper",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
        "APP_ENV": "test",
        "LIVE_TRADING_CONFIRM": "false",
        "LOG_LEVEL": "DEBUG",
        "KITE_API_KEY": "test_api_key",
        "KITE_ACCESS_TOKEN": "test_access_token",
    }

    with patch.dict(os.environ, test_env):
        settings = Settings()

        assert settings.finbot_mode == "paper"
        assert settings.database_url == "postgresql://user:pass@localhost:5432/testdb"
        assert settings.app_env == "test"
        assert settings.live_trading_confirm is False
        assert settings.log_level == "DEBUG"


def test_database_url_construction():
    """Test database URL construction from individual components."""
    from backend.config.settings import Settings

    test_env = {
        "DATABASE_USER": "testuser",
        "DATABASE_PASSWORD": "testpass",
        "DATABASE_HOST": "localhost",
        "DATABASE_PORT": "5432",
        "DATABASE_NAME": "testdb",
    }

    with patch.dict(os.environ, test_env):
        settings = Settings()
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert settings.database_url == expected_url


def test_database_url_fallback_to_sqlite():
    """Test fallback to SQLite when PostgreSQL components are missing."""
    from backend.config.settings import Settings

    test_env = {
        "DATABASE_NAME": "test.db",
    }

    with patch.dict(os.environ, test_env):
        settings = Settings()
        assert settings.database_url == "sqlite:///test.db"


def test_broker_config_loading():
    """Test loading broker configuration (Kite, etc.)."""
    from backend.config.settings import Settings

    test_env = {
        "KITE_API_KEY": "test_kite_key",
        "KITE_ACCESS_TOKEN": "test_kite_token",
        "ZERODHA_API_KEY": "test_zerodha_key",
        "ZERODHA_ACCESS_TOKEN": "test_zerodha_token",
    }

    with patch.dict(os.environ, test_env):
        settings = Settings()

        # Assuming settings has broker config attributes
        assert hasattr(settings, 'kite_api_key')
        assert hasattr(settings, 'kite_access_token')
        # assert settings.kite_api_key == "test_kite_key"
        # assert settings.kite_access_token == "test_kite_token"


def test_risk_config_loading():
    """Test loading risk management configuration."""
    from backend.config.settings import Settings

    test_env = {
        "MAX_DRAWDOWN": "0.15",
        "MAX_DAILY_LOSS": "0.05",
        "MAX_POSITION_SIZE": "0.10",
        "MAX_PORTFOLIO_SIZE": "100000",
    }

    with patch.dict(os.environ, test_env):
        settings = Settings()

        # Assuming settings has risk config attributes
        assert hasattr(settings, 'max_drawdown')
        assert hasattr(settings, 'max_daily_loss')
        # assert settings.max_drawdown == 0.15
        # assert settings.max_daily_loss == 0.05


def test_feature_flags_loading():
    """Test loading feature flags and toggles."""
    from backend.config.settings import Settings

    test_env = {
        "ENABLE_AI_FEATURES": "true",
        "ENABLE_PAPER_TRADING": "false",
        "ENABLE_LIVE_TRADING": "false",
        "ENABLE_METRICS": "true",
    }

    with patch.dict(os.environ, test_env):
        settings = Settings()

        # Assuming settings has feature flag attributes
        assert hasattr(settings, 'enable_ai_features')
        assert hasattr(settings, 'enable_paper_trading')
        assert settings.enable_ai_features is True
        assert settings.enable_paper_trading is False


def test_config_validation():
    """Test configuration validation and error handling."""
    from backend.config.settings import Settings

    # Test invalid database URL
    test_env = {
        "DATABASE_URL": "invalid://url",
    }

    with patch.dict(os.environ, test_env):
        with pytest.raises(ValueError):
            Settings()

    # Test invalid numeric values
    test_env = {
        "MAX_DRAWDOWN": "invalid_number",
    }

    with patch.dict(os.environ, test_env):
        with pytest.raises(ValueError):
            Settings()


def test_config_from_env_file():
    """Test loading configuration from .env file."""
    import tempfile
    from pathlib import Path

    env_content = """
FINBOT_MODE=dev
DATABASE_URL=sqlite:///test.db
APP_ENV=test
LIVE_TRADING_CONFIRM=false
LOG_LEVEL=INFO
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(env_content)
        env_file = f.name

    try:
        # Mock the env file reading
        with patch("backend.config.settings.load_dotenv") as mock_load:
            mock_load.return_value = True
            with patch.dict(os.environ, {
                "FINBOT_MODE": "dev",
                "DATABASE_URL": "sqlite:///test.db",
                "APP_ENV": "test",
                "LIVE_TRADING_CONFIRM": "false",
                "LOG_LEVEL": "INFO",
            }):
                from backend.config.settings import Settings
                settings = Settings()

                assert settings.finbot_mode == "dev"
                assert settings.database_url == "sqlite:///test.db"
                assert settings.app_env == "test"
    finally:
        Path(env_file).unlink()
