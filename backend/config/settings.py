from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Literal, Sequence

from pydantic import ConfigDict, Field, model_validator
from pydantic.functional_validators import field_validator
from pydantic_settings import BaseSettings

from common.env import expand_env_vars

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class BackendSettings(BaseSettings):
    """Environment-driven settings for the Finbot backend."""

    # Modes:
    # - dev: safe sandbox, mock/test data
    # - paper: paper-trading or broker sandbox
    # - live: real orders; requires FINBOT_LIVE_TRADING_CONFIRM=true
    finbot_mode: Literal["dev", "paper", "live"] = Field("dev", env="FINBOT_MODE")
    live_trading_confirm: bool = Field(False, env="FINBOT_LIVE_TRADING_CONFIRM")
    app_use_case: str = Field("PERSONAL_EXPERIMENTAL", env="APP_USE_CASE")

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
    log_dir: str = Field("logs", env="LOG_DIR")
    log_filename: str = Field("finbot.log", env="LOG_FILENAME")
    log_file: str | None = Field(None, env="LOG_FILE")
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

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow")

    @field_validator("allow_origins", mode="before")
    def _parse_allow_origins(cls, value: Sequence[str] | str) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return list(value)

    @field_validator("default_symbols", mode="before")
    def _parse_default_symbols(cls, value: Sequence[str] | str) -> List[str]:
        if isinstance(value, str):
            return [symbol.strip() for symbol in value.split(",") if symbol.strip()]
        return list(value)

    @staticmethod
    def _resolve_path(value: str, base: Path | None = None) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            prefix = base or PROJECT_ROOT
            candidate = prefix / candidate
        return candidate.resolve()

    @model_validator(mode="after")
    def _finalize_log_paths(self) -> "BackendSettings":
        self._apply_env_expansion()
        log_dir_path = self._resolve_path(self.log_dir or "logs")

        if self.log_file:
            file_candidate = Path(self.log_file).expanduser()
            if not file_candidate.is_absolute():
                file_candidate = (log_dir_path / self.log_file).resolve()
            else:
                file_candidate = file_candidate.resolve()
        else:
            file_candidate = (log_dir_path / self.log_filename).resolve()

        self.log_file = str(file_candidate)
        self.log_dir = str(file_candidate.parent)
        return self

    def _apply_env_expansion(self) -> None:
        for field_name in getattr(self, "model_fields", {}):
            value = getattr(self, field_name)
            object.__setattr__(self, field_name, expand_env_vars(value))


settings = BackendSettings()

# Backwards compatibility for older imports
Settings = BackendSettings


def get_settings() -> BackendSettings:
    """Return cached backend settings instance."""
    return settings
