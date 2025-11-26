from __future__ import annotations

from typing import Any, Dict, List, Literal, Sequence

try:
    # Prefer pydantic v1-style import
    from pydantic import BaseSettings  # type: ignore
except Exception:  # pragma: no cover - executed under Pydantic v2
    try:
        from pydantic_settings import BaseSettings  # type: ignore
    except Exception:
        # Fallback to BaseModel to keep runtime working in minimal environments
        from pydantic import BaseModel as BaseSettings  # type: ignore

from pydantic import Field, validator

DEFAULT_ORIGINS = ["http://localhost:8501", "http://localhost:5173", "http://localhost:3000"]
DEFAULT_NEWS_SOURCES = [
    {
        "name": "WSJ Markets",
        "type": "rss",
        "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "symbols": ["AAPL", "MSFT", "NVDA"],
    },
    {
        "name": "Finviz",
        "type": "rss",
        "url": "https://finviz.com/feed.ashx",
        "symbols": ["SPY", "QQQ"],
    },
]


class BackendSettings(BaseSettings):
    """Environment-driven settings for the Finbot backend."""

    # Modes:
    # - dev: safe sandbox, mock/test data
    # - paper: paper-trading or broker sandbox
    # - live: real orders; requires FINBOT_LIVE_TRADING_CONFIRM=true
    finbot_mode: Literal["dev", "paper", "live"] = Field("dev", env="FINBOT_MODE")
    live_trading_confirm: bool = Field(False, env="FINBOT_LIVE_TRADING_CONFIRM")

    app_env: str = Field("development", env="APP_ENV")
    app_name: str = Field("Finbot Trading API", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    allow_origins: Sequence[str] = Field(DEFAULT_ORIGINS, env="ALLOW_ORIGINS")

    database_url: str | None = Field(None, env="DATABASE_URL")
    database_host: str = Field("localhost", env="DATABASE_HOST")
    database_port: int = Field(5432, env="DATABASE_PORT")
    database_name: str = Field("finbot_db", env="DATABASE_NAME")
    database_user: str = Field("finbot_user", env="DATABASE_USER")
    database_password: str | None = Field(None, env="DATABASE_PASSWORD")

    redis_url: str | None = Field(None, env="REDIS_URL")
    cache_ttl_seconds: int = Field(60, env="CACHE_TTL_SECONDS")
    sentry_dsn: str | None = Field(None, env="SENTRY_DSN")

    jwt_secret_key: str = Field("change-me", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")

    trading_mode: str = Field("simulation", env="TRADING_MODE")
    update_interval_seconds: float = Field(5.0, env="UPDATE_INTERVAL_SECONDS")
    default_symbols: Sequence[str] = Field(("AAPL", "GOOGL", "MSFT"), env="DEFAULT_SYMBOLS")

    max_drawdown: float = Field(0.15, env="MAX_DRAWDOWN")
    max_daily_loss: float = Field(0.05, env="MAX_DAILY_LOSS")
    max_position_size: float = Field(0.1, env="MAX_POSITION_SIZE")
    initial_cash: float = Field(100000.0, env="INITIAL_CASH")

    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/finbot.log", env="LOG_FILE")
    log_max_size: int = Field(10_485_760, env="LOG_MAX_SIZE")
    log_backup_count: int = Field(5, env="LOG_BACKUP_COUNT")

    health_check_interval: int = Field(30, env="HEALTH_CHECK_INTERVAL")
    metrics_retention_days: int = Field(30, env="METRICS_RETENTION_DAYS")
    enable_prometheus_metrics: bool = Field(False, env="ENABLE_PROMETHEUS_METRICS")
    prometheus_port: int = Field(9090, env="PROMETHEUS_PORT")

    news_database_url: str | None = Field(None, env="NEWS_DATABASE_URL")
    news_enable_ai: bool = Field(True, env="NEWS_ENABLE_AI")
    news_max_articles: int = Field(25, env="NEWS_MAX_ARTICLES")
    news_scheduler_run_time: str = Field("06:00", env="NEWS_SCHEDULER_RUN_TIME")
    news_scheduler_timezone: str = Field("UTC", env="NEWS_SCHEDULER_TIMEZONE")
    news_scheduler_enabled: bool = Field(True, env="NEWS_SCHEDULER_ENABLED")
    news_sources: List[Dict[str, Any]] = Field(DEFAULT_NEWS_SOURCES, env="NEWS_SOURCES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("allow_origins", pre=True)
    def _parse_allow_origins(cls, value: Sequence[str] | str) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return list(value)

    @validator("default_symbols", pre=True)
    def _parse_default_symbols(cls, value: Sequence[str] | str) -> List[str]:
        if isinstance(value, str):
            return [symbol.strip() for symbol in value.split(",") if symbol.strip()]
        return list(value)


settings = BackendSettings()
