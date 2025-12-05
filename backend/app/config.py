"""Centralized application configuration for the backend service."""

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings

from common.env import expand_env_vars

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration pulled from environment variables.

    Modes: dev = safe sandbox/mock data; paper = broker sandbox/paper trading;
    live = real brokers and requires FINBOT_LIVE_TRADING_CONFIRM=true.
    """

    finbot_mode: Literal["dev", "paper", "live"] = Field("dev", env="FINBOT_MODE")
    live_trading_confirm: bool = Field(False, env="FINBOT_LIVE_TRADING_CONFIRM")

    app_name: str = "Finbot Backend"
    environment: str = "development"
    database_url: str = "sqlite:///./market_data.db"
    redis_url: str | None = None
    cache_ttl_seconds: int = 30
    uvicorn_workers: int = 2
    sentry_dsn: str | None = None
    allow_origins: list[str] = [
        "http://localhost:1420",
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_dir: str = Field("logs", env="LOG_DIR")
    log_filename: str = Field("finbot.log", env="LOG_FILENAME")
    log_file: str | None = Field(None, env="LOG_FILE")
    log_max_bytes: int = Field(10_485_760, env="LOG_MAX_SIZE")
    log_backup_count: int = Field(5, env="LOG_BACKUP_COUNT")
    log_scan_limit: int = Field(2000, env="LOG_SCAN_LIMIT")

    enforce_https: bool = Field(default=False, env="ENFORCE_HTTPS")

    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    default_admin_username: str = Field(default="admin", env="DEFAULT_ADMIN_USERNAME")
    default_admin_password: str = Field(default="adminpass", env="DEFAULT_ADMIN_PASSWORD")
    default_user_username: str = Field(default="user", env="DEFAULT_USER_USERNAME")
    default_user_password: str = Field(default="userpass", env="DEFAULT_USER_PASSWORD")

    # Model configuration for pydantic v2
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @staticmethod
    def _resolve_path(value: str, base: Path | None = None) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            prefix = base or PROJECT_ROOT
            candidate = prefix / candidate
        return candidate.resolve()

    @model_validator(mode="after")
    def _finalize_log_paths(self) -> "Settings":
        self._apply_env_expansion()
        log_dir_path = self._resolve_path(self.log_dir or "logs")

        if self.log_file:
            file_candidate = Path(self.log_file).expanduser()
            if not file_candidate.is_absolute():
                file_candidate = self._resolve_path(self.log_file, log_dir_path)
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


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
