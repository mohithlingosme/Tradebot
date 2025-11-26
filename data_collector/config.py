from __future__ import annotations

"""
Shared settings for Phase 3 data collection components.
"""

import os
from functools import lru_cache
from typing import Dict, List, Literal, Sequence
from pydantic import Field

try:  # Prefer pydantic-settings if present
    from pydantic_settings import BaseSettings  # type: ignore
except Exception:  # pragma: no cover - fallback for environments without pydantic-settings
    from pydantic import BaseSettings  # type: ignore


def _resolve_default_db_url() -> str:
    """
    Resolve the database URL from environment variables or backend settings as a fallback.
    """
    env_url = os.getenv("DATA_COLLECTOR_DATABASE_URL") or os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    try:
        from backend.config import settings as backend_settings  # type: ignore

        if backend_settings.database_url:
            return backend_settings.database_url
    except Exception:
        pass

    return "postgresql://finbot_user:finbot_password@localhost:5432/finbot_db"


DEFAULT_SYMBOLS = (
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
)


DEFAULT_SECTOR_INDICES: Dict[str, str] = {
    "NIFTY_50": "^NSEI",
    "NIFTY_BANK": "^NSEBANK",
    "NIFTY_IT": "^CNXIT",
    "NIFTY_FMCG": "^CNXFMCG",
    "NIFTY_AUTO": "^CNXAUTO",
}


class DataCollectorSettings(BaseSettings):
    """
    Environment-driven configuration for the data collector layer.
    """

    # Modes: dev (safe sandbox), paper (paper-trading/broker sandbox), live (real brokers; requires confirmation)
    finbot_mode: Literal["dev", "paper", "live"] = Field("dev", env="FINBOT_MODE")
    live_trading_confirm: bool = Field(False, env="FINBOT_LIVE_TRADING_CONFIRM")

    database_url: str = Field(default_factory=_resolve_default_db_url)
    symbols_file: str | None = Field(
        default=None, description="Optional path to a newline-delimited list of symbols"
    )
    default_symbols: Sequence[str] = Field(DEFAULT_SYMBOLS, description="Fallback NSE symbols")
    sector_indices: Dict[str, str] = Field(
        DEFAULT_SECTOR_INDICES, description="Mapping of sector index names to tickers"
    )

    news_api_key: str | None = Field(default=None, env="NEWS_API_KEY")
    news_api_endpoint: str = Field("https://newsapi.org/v2/everything", env="NEWS_API_ENDPOINT")
    gnews_api_key: str | None = Field(default=None, env="GNEWS_API_KEY")
    news_page_size: int = Field(50, description="Pagination size for news API calls")
    news_market_terms: Sequence[str] = Field(
        ("Nifty 50", "Nifty Bank", "Sensex", "RBI", "Federal Reserve"),
        description="Generic market search terms",
    )

    sentiment_provider: str = Field("vader", description="Sentiment engine to use")
    article_dedupe_horizon_days: int = Field(
        7, description="Deduplicate identical URLs within this many days"
    )

    macro_provider: str = Field("yfinance", description="Macro data provider")
    fundamentals_provider: str = Field("yfinance", description="Fundamentals data provider")

    feature_output_dir: str = Field("data/features", description="Local feature storage directory")
    feature_version: str = Field("v1", description="Feature set version identifier")

    scheduler_enabled: bool = Field(True, description="Toggle APScheduler on/off")
    scheduler_timezone: str = Field("Asia/Kolkata", description="Scheduler timezone")
    scheduler_daily_time: str = Field("06:30", description="HH:MM time to run daily jobs")
    scheduler_weekly_day: str = Field("sun", description="Cron-style day for weekly jobs")

    log_level: str = Field("INFO", description="Default log level")
    request_timeout_seconds: int = Field(30, description="HTTP client timeout")

    class Config:
        env_file = ".env"
        env_prefix = "DATA_COLLECTOR_"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> DataCollectorSettings:
    """Cached settings accessor."""
    return DataCollectorSettings()
