from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseSettings, Field, validator

DEFAULT_PROVIDER_CONFIGS = {
    "yfinance": {"is_active": True, "rate_limit_per_minute": 100},
    "alphavantage": {
        "is_active": True,
        "api_key": "${ALPHAVANTAGE_API_KEY}",
        "base_url": "https://www.alphavantage.co",
        "rate_limit_per_minute": 5,
    },
    "kite_ws": {
        "is_active": True,
        "api_key": "${KITE_API_KEY}",
        "api_secret": "${KITE_API_SECRET}",
        "websocket_url": "ws://localhost:8765",
        "reconnect_interval": 5,
        "heartbeat_interval": 30,
    },
    "mock": {
        "is_active": True,
        "websocket_url": "ws://localhost:8765",
        "api_key": "mock",
        "api_secret": "mock",
        "reconnect_interval": 5,
        "heartbeat_interval": 30,
    },
}


class MarketDataSettings(BaseSettings):
    """Shared configuration for the market data ingestion stack."""

    app_env: str = Field("development", env="APP_ENV")
    database_url: str = Field("sqlite:///market_data.db", env="MARKET_DATA_DATABASE_URL")
    config_path: Path = Field(
        Path("market_data_ingestion/config/config.example.yaml"),
        env="MARKET_DATA_CONFIG_PATH",
    )

    log_level: str = Field("INFO", env="LOG_LEVEL")
    api_port: int = Field(8001, env="APP_PORT")
    health_port: int = Field(8080, env="MARKET_DATA_HEALTH_PORT")
    metrics_port: int = Field(9090, env="MARKET_DATA_METRICS_PORT")
    enable_metrics: bool = Field(True, env="ENABLE_PROMETHEUS_METRICS")

    provider_configs: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: DEFAULT_PROVIDER_CONFIGS.copy())
    instruments: List[Dict[str, str]] = Field(default_factory=list)

    scheduler_run_time: str = Field("02:00", env="MARKET_DATA_SCHEDULER_RUN_TIME")
    scheduler_timezone: str = Field("UTC", env="MARKET_DATA_SCHEDULER_TIMEZONE")
    scheduler_period: str | None = Field(None, env="MARKET_DATA_SCHEDULER_PERIOD")
    scheduler_interval: str | None = Field(None, env="MARKET_DATA_SCHEDULER_INTERVAL")
    scheduler_symbols: List[str] | None = Field(None, env="MARKET_DATA_SCHEDULER_SYMBOLS")
    scheduler_enabled: bool = Field(True, env="MARKET_DATA_SCHEDULER_ENABLED")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("scheduler_symbols", pre=True)
    def _parse_scheduler_symbols(cls, value):
        if isinstance(value, str):
            return [symbol.strip() for symbol in value.split(",") if symbol.strip()]
        return value

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        object.__setattr__(self, "provider_configs", self._expand_env_vars(self.provider_configs))
        self._load_yaml_overrides()

    def _load_yaml_overrides(self) -> None:
        config = self._read_yaml_config()
        if not config:
            return

        database_cfg = config.get("database", {})
        if database_cfg.get("db_path"):
            object.__setattr__(self, "database_url", database_cfg["db_path"])

        providers = config.get("providers")
        if providers:
            merged = {**DEFAULT_PROVIDER_CONFIGS, **providers}
            object.__setattr__(self, "provider_configs", self._expand_env_vars(merged))

        instruments = config.get("instruments")
        if isinstance(instruments, list):
            object.__setattr__(self, "instruments", instruments)

        scheduler_cfg = config.get("scheduler", {}).get("auto_refresh", {})
        if scheduler_cfg.get("run_time"):
            object.__setattr__(self, "scheduler_run_time", scheduler_cfg["run_time"])
        if scheduler_cfg.get("timezone"):
            object.__setattr__(self, "scheduler_timezone", scheduler_cfg["timezone"])
        if scheduler_cfg.get("period"):
            object.__setattr__(self, "scheduler_period", scheduler_cfg["period"])
        if scheduler_cfg.get("interval"):
            object.__setattr__(self, "scheduler_interval", scheduler_cfg["interval"])
        if scheduler_cfg.get("symbols"):
            object.__setattr__(self, "scheduler_symbols", scheduler_cfg["symbols"])
        if "enabled" in scheduler_cfg:
            object.__setattr__(self, "scheduler_enabled", scheduler_cfg["enabled"])

    def _read_yaml_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        import yaml

        try:
            with self.config_path.open(encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
        except Exception:
            return {}

    def provider_config(self, name: str) -> Dict[str, Any] | None:
        """Helper to return a deserialized provider configuration."""
        return self.provider_configs.get(name)

    def _expand_env_vars(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._expand_env_vars(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]
        if isinstance(value, str):
            pattern = re.compile(r"\$\{([^}]+)\}")

            def replace(match: re.Match[str]) -> str:
                env_value = os.getenv(match.group(1))
                return env_value if env_value is not None else match.group(0)

            return pattern.sub(replace, value)
        return value


settings = MarketDataSettings()


def get_settings() -> MarketDataSettings:
    """Return the shared settings instance."""
    return settings
