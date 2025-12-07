from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Dict, List, Literal, Sequence, Set, Callable

from pydantic import Field, model_validator
from pydantic.functional_validators import field_validator
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsSourceCallable
except ImportError:
    from pydantic import BaseModel as BaseSettings
    SettingsConfigDict = dict
    SettingsSourceCallable = Callable[[BaseSettings], Dict[str, Any]]

from common.env import expand_env_vars
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False

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
_ENV_FILE_KEYS: Set[str] = set()
_ENV_FILE_OVERRIDES: Dict[str, str] = {}
_TRUTHY = {"true", "1", "yes", "y", "on"}
_FALSY = {"false", "0", "no", "n", "off"}
_ENV_ALIAS_MAP: Dict[str, str] = {
    "FINBOT_LIVE_TRADING_CONFIRM": "LIVE_TRADING_CONFIRM",
}
_ALWAYS_OVERRIDE_KEYS = {"FINBOT_MODE", "FINBOT_LIVE_TRADING_CONFIRM"}
_LAST_ENV_VALUES: Dict[str, str] = {}


def _should_inject_from_file(key: str) -> bool:
    env_value = os.getenv(key)
    if env_value is None:
        return True
    file_value = _ENV_FILE_OVERRIDES.get(key)
    if file_value is None:
        return False
    return env_value == file_value


def _coerce_bool(value: str | bool | None) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).split("#", 1)[0].strip().lower()
    if normalized in _TRUTHY:
        return True
    if normalized in _FALSY:
        return False
    return None


def _resolve_live_trading_confirm() -> bool | None:
    for key in ("FINBOT_LIVE_TRADING_CONFIRM", "LIVE_TRADING_CONFIRM"):
        parsed = _coerce_bool(os.getenv(key))
        if parsed is not None:
            return parsed
    if _should_inject_from_file("FINBOT_LIVE_TRADING_CONFIRM"):
        return _coerce_bool(_LAST_ENV_VALUES.get("FINBOT_LIVE_TRADING_CONFIRM"))
    return None


def _resolve_finbot_mode() -> str | None:
    value = os.getenv("FINBOT_MODE")
    if value and "FINBOT_MODE" not in _ENV_FILE_OVERRIDES:
        return value.strip().lower()
    if _should_inject_from_file("FINBOT_MODE"):
        file_value = _LAST_ENV_VALUES.get("FINBOT_MODE")
        if file_value:
            return file_value.strip().lower()
    if value:
        return value.strip().lower()
    return None


def _track_env_override(key: str, value: str | None) -> None:
    if value is None:
        return
    _ENV_FILE_KEYS.add(key)
    _ENV_FILE_OVERRIDES[key] = value


def _release_env_override(key: str) -> None:
    _ENV_FILE_KEYS.discard(key)
    _ENV_FILE_OVERRIDES.pop(key, None)


def _sync_env_overrides() -> None:
    for key, recorded in list(_ENV_FILE_OVERRIDES.items()):
        current = os.getenv(key)
        if current is None:
            continue
        if current != recorded:
            _release_env_override(key)


def _get_env_loader():
    try:
        from scripts.dev_run import read_env_file as loader

        return loader
    except Exception:  # pragma: no cover - optional dependency
        return _default_read_env_file


def _default_read_env_file(env_path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not env_path.exists():
        return env
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def _load_mode_env() -> None:
    """Load .env.<mode> to mirror scripts.dev_run behavior in tests."""
    loader = _get_env_loader()
    mode = (os.getenv("FINBOT_MODE") or "dev").strip().lower()
    env_file = PROJECT_ROOT / f".env.{mode}"
    values = loader(env_file)
    _sync_env_overrides()
    global _LAST_ENV_VALUES
    _LAST_ENV_VALUES = dict(values)
    if not values:
        return
    for key, value in values.items():
        if value is None:
            continue
        if key in _ALWAYS_OVERRIDE_KEYS:
            current_value = os.getenv(key)
            should_apply = (
                current_value is None
                or key in _ENV_FILE_KEYS
                or (current_value == value)
            )
            if should_apply:
                os.environ[key] = value
                _track_env_override(key, value)
            else:
                _release_env_override(key)


def _apply_env_aliases() -> None:
    """Mirror legacy FINBOT_* env names into BaseSettings-compatible keys."""
    _sync_env_overrides()
    for source, target in _ENV_ALIAS_MAP.items():
        value = os.getenv(source)
        if value is None:
            continue
        if target not in os.environ or target in _ENV_FILE_KEYS:
            os.environ[target] = value
            _track_env_override(target, value)
        else:
            _release_env_override(target)

ALLOWED_DB_SCHEMES = {
    "postgresql",
    "postgresql+psycopg",
    "postgresql+asyncpg",
    "sqlite",
    "mysql",
    "mariadb",
}


class BackendSettings(BaseSettings):
    """Environment-driven settings for the Finbot backend."""

    # Modes:
    # - dev: safe sandbox, mock/test data
    # - paper: paper-trading or broker sandbox
    # - live: real orders; requires FINBOT_LIVE_TRADING_CONFIRM=true
    finbot_mode: Literal["dev", "paper", "live"] = Field("dev")
    live_trading_confirm: bool = Field(False)
    app_use_case: str = Field("PERSONAL_EXPERIMENTAL")

    app_env: str = Field("development")
    app_name: str = Field("Finbot Trading API")
    app_version: str = Field("1.0.0")
    app_host: str = Field("0.0.0.0")
    app_port: int = Field(8000)
    allow_origins: Sequence[str] = Field(DEFAULT_ORIGINS)

    database_url: str | None = Field(None)
    database_host: str = Field("localhost")
    database_port: int = Field(5432)
    database_name: str = Field("finbot_db")
    database_user: str = Field("finbot_user")
    database_password: str | None = Field(None)

    redis_url: str | None = Field(None)
    cache_ttl_seconds: int = Field(60)
    sentry_dsn: str | None = Field(None)

    jwt_secret_key: str = Field("change-me")
    jwt_algorithm: str = Field("HS256")

    trading_mode: str = Field("simulation")
    update_interval_seconds: float = Field(5.0)
    default_symbols: Sequence[str] = Field(("AAPL", "GOOGL", "MSFT"))

    max_drawdown: float = Field(0.15)
    max_daily_loss: float = Field(0.05)
    max_position_size: float = Field(0.1)
    initial_cash: float = Field(100000.0)

    # Feature flags / broker config
    enable_ai_features: bool = Field(True)
    enable_paper_trading: bool = Field(True)
    enable_live_trading: bool = Field(False)
    enable_metrics: bool = Field(True)
    kite_api_key: str | None = Field(None)
    kite_access_token: str | None = Field(None)
    zerodha_api_key: str | None = Field(None)
    zerodha_access_token: str | None = Field(None)

    log_level: str = Field("INFO")
    log_dir: str = Field("logs")
    log_filename: str = Field("finbot.log")
    log_file: str | None = Field(None)
    log_max_size: int = Field(10_485_760)
    log_backup_count: int = Field(5)

    health_check_interval: int = Field(30)
    metrics_retention_days: int = Field(30)
    enable_prometheus_metrics: bool = Field(False)
    prometheus_port: int = Field(9090)

    news_database_url: str | None = Field(None)
    news_enable_ai: bool = Field(True)
    news_max_articles: int = Field(25)
    news_scheduler_run_time: str = Field("06:00")
    news_scheduler_timezone: str = Field("UTC")
    news_scheduler_enabled: bool = Field(True)
    news_sources: List[Dict[str, Any]] = Field(DEFAULT_NEWS_SOURCES)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type["BackendSettings"],
        init_settings: SettingsSourceCallable,
        env_settings: SettingsSourceCallable,
        dotenv_settings: SettingsSourceCallable,
        file_secret_settings: SettingsSourceCallable,
    ) -> tuple[SettingsSourceCallable, ...]:
        def prepare_mode(_: BaseSettings | None = None) -> Dict[str, Any]:
            _load_mode_env()
            _apply_env_aliases()
            return {}

        def mode_env_settings(_: BaseSettings | None = None) -> Dict[str, Any]:
            payload: Dict[str, Any] = {}

            mode_value = os.getenv("FINBOT_MODE")
            if mode_value is None and _should_inject_from_file("FINBOT_MODE"):
                mode_value = _LAST_ENV_VALUES.get("FINBOT_MODE")
            if mode_value is not None:
                payload["finbot_mode"] = mode_value

            confirm_value = os.getenv("FINBOT_LIVE_TRADING_CONFIRM")
            if confirm_value is None and _should_inject_from_file("FINBOT_LIVE_TRADING_CONFIRM"):
                confirm_value = _LAST_ENV_VALUES.get("FINBOT_LIVE_TRADING_CONFIRM")
            if confirm_value is not None:
                normalized = str(confirm_value).strip().lower()
                payload["live_trading_confirm"] = normalized in {"true", "1", "yes", "y"}

            return payload

        return (
            init_settings,
            prepare_mode,
            env_settings,
            mode_env_settings,
            dotenv_settings,
            file_secret_settings,
        )

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

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str | None) -> str | None:
        if not value:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in ALLOWED_DB_SCHEMES:
            raise ValueError(f"Unsupported database scheme: {parsed.scheme}")
        if parsed.scheme != "sqlite" and not parsed.hostname:
            raise ValueError("Database URL must include a hostname")
        if parsed.scheme != "sqlite" and not parsed.path.strip("/"):
            raise ValueError("Database URL must include a database name")
        return value

    @staticmethod
    def _resolve_path(value: str, base: Path | None = None) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            prefix = base or PROJECT_ROOT
            candidate = prefix / candidate
        return candidate.resolve()

    @model_validator(mode="after")
    def _finalize_settings(self) -> "BackendSettings":
        mode_override = _resolve_finbot_mode()
        if mode_override:
            object.__setattr__(self, "finbot_mode", mode_override)
        confirm_override = _resolve_live_trading_confirm()
        if confirm_override is not None:
            object.__setattr__(self, "live_trading_confirm", confirm_override)
        if self.finbot_mode == "live" and not self.live_trading_confirm:
            object.__setattr__(self, "finbot_mode", "paper")
        self._apply_env_expansion()
        self._ensure_database_url()
        self._finalize_log_paths()
        return self

    def _finalize_log_paths(self) -> None:
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

    def _ensure_database_url(self) -> None:
        if self.database_url:
            return

        # Use PostgreSQL style URL unless the name looks like a SQLite file
        database_name = self.database_name.strip()
        if database_name.endswith(".db") or "/" in database_name:
            path = database_name if database_name.endswith(".db") else f"{database_name}.db"
            self.database_url = f"sqlite:///{path}"
            return

        user_part = self.database_user
        if self.database_password:
            user_part = f"{user_part}:{self.database_password}"
        self.database_url = (
            f"postgresql://{user_part}@{self.database_host}:{self.database_port}/{database_name}"
        )

    def _apply_env_expansion(self) -> None:
        model_fields = getattr(self.__class__, "model_fields", {})
        for field_name in model_fields:
            value = getattr(self, field_name)
            object.__setattr__(self, field_name, expand_env_vars(value))


_BASE_ENVIRONMENT = dict(os.environ)
load_dotenv()
for _key in _ALWAYS_OVERRIDE_KEYS:
    if _key not in _BASE_ENVIRONMENT and _key in os.environ:
        _track_env_override(_key, os.environ[_key])
settings = BackendSettings()

# Backwards compatibility for older imports
Settings = BackendSettings


def get_settings() -> BackendSettings:
    """Return cached backend settings instance."""
    return settings
