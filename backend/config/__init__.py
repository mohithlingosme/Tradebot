from __future__ import annotations

from typing import Any, Dict

from .settings import settings

__all__ = ["load_config", "get_config", "settings"]

_config: Dict[str, Any] | None = None


def load_config(env: str | None = None) -> Dict[str, Any]:
    """
    Build a configuration dictionary for legacy consumers while keeping
    the BaseSettings-backed `settings` instance as the primary source of
    truth.
    """
    active_env = env or settings.app_env
    database_info = {
        "url": settings.database_url,
        "host": settings.database_host,
        "port": settings.database_port,
        "name": settings.database_name,
        "user": settings.database_user,
        "password": settings.database_password,
    }

    if not database_info["url"]:
        database_info["url"] = f"sqlite:///{settings.database_name}.db"

    news_db_url = settings.news_database_url or settings.database_url or f"sqlite:///{settings.database_name}_news.db"

    config: Dict[str, Any] = {
        "app": {
            "env": active_env,
            "port": settings.app_port,
            "host": settings.app_host,
            "cors_origins": list(settings.allow_origins),
            "name": settings.app_name,
            "version": settings.app_version,
        },
        "database": database_info,
        "redis": {
            "url": settings.redis_url,
        },
        "auth": {
            "jwt_secret_key": settings.jwt_secret_key,
            "jwt_algorithm": settings.jwt_algorithm,
            "access_token_expire_minutes": 30,
        },
        "trading": {
            "mode": settings.trading_mode,
            "update_interval_seconds": settings.update_interval_seconds,
            "default_symbols": list(
                settings.default_symbols
            ),
        },
        "risk": {
            "max_drawdown": settings.max_drawdown,
            "max_daily_loss": settings.max_daily_loss,
            "max_position_size": settings.max_position_size,
            "initial_cash": settings.initial_cash,
        },
        "logging": {
            "level": settings.log_level,
            "file": settings.log_file,
            "max_size": settings.log_max_size,
            "backup_count": settings.log_backup_count,
        },
        "monitoring": {
            "health_check_interval": settings.health_check_interval,
            "metrics_retention_days": settings.metrics_retention_days,
            "enable_prometheus": settings.enable_prometheus_metrics,
            "prometheus_port": settings.prometheus_port,
        },
        "news": {
            "database_url": news_db_url,
            "enable_ai": settings.news_enable_ai,
            "max_articles": settings.news_max_articles,
            "sources": settings.news_sources,
            "scheduler": {
                "enabled": settings.news_scheduler_enabled,
                "run_time": settings.news_scheduler_run_time,
                "timezone": settings.news_scheduler_timezone,
            },
        },
    }

    return config


def get_config() -> Dict[str, Any]:
    """Return the cached configuration dictionary for legacy consumers."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
