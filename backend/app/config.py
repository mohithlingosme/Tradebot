"""Centralized application configuration for the backend service."""

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


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
    log_file: str = Field("logs/finbot.log", env="LOG_FILE")
    log_max_bytes: int = Field(10_485_760, env="LOG_MAX_SIZE")
    log_backup_count: int = Field(5, env="LOG_BACKUP_COUNT")
    log_scan_limit: int = Field(2000, env="LOG_SCAN_LIMIT")

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
