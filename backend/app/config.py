"""Centralized application configuration for the backend service."""

from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration pulled from environment variables."""

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
