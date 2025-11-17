"""
Configuration module for Finbot Backend.

Provides environment-specific configuration management.
"""

import os
from typing import Dict, Any
from pathlib import Path

def load_config(env: str = None) -> Dict[str, Any]:
    """
    Load configuration based on environment.

    Args:
        env: Environment name (development, staging, production)

    Returns:
        Configuration dictionary
    """
    if env is None:
        env = os.getenv("APP_ENV", "development")

    # Base configuration
    config = {
        "app": {
            "env": env,
            "port": int(os.getenv("APP_PORT", "8000")),
            "host": os.getenv("APP_HOST", "0.0.0.0"),
            "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")
        },
        "database": {
            "url": os.getenv("DATABASE_URL"),
            "host": os.getenv("DATABASE_HOST", "localhost"),
            "port": int(os.getenv("DATABASE_PORT", "5432")),
            "name": os.getenv("DATABASE_NAME", "finbot_db"),
            "user": os.getenv("DATABASE_USER", "finbot_user"),
            "password": os.getenv("DATABASE_PASSWORD")
        },
        "redis": {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD")
        },
        "auth": {
            "jwt_secret_key": os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"),
            "jwt_algorithm": "HS256",
            "access_token_expire_minutes": 30
        },
        "trading": {
            "mode": os.getenv("TRADING_MODE", "simulation"),
            "update_interval_seconds": float(os.getenv("UPDATE_INTERVAL_SECONDS", "5.0")),
            "default_symbols": os.getenv("DEFAULT_SYMBOLS", "AAPL,GOOGL,MSFT").split(",")
        },
        "risk": {
            "max_drawdown": float(os.getenv("MAX_DRAWDOWN", "0.15")),
            "max_daily_loss": float(os.getenv("MAX_DAILY_LOSS", "0.05")),
            "max_position_size": float(os.getenv("MAX_POSITION_SIZE", "0.10")),
            "initial_cash": float(os.getenv("INITIAL_CASH", "100000"))
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file": os.getenv("LOG_FILE", "logs/finbot.log"),
            "max_size": int(os.getenv("LOG_MAX_SIZE", "10485760")),
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
        },
        "monitoring": {
            "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            "metrics_retention_days": int(os.getenv("METRICS_RETENTION_DAYS", "30")),
            "enable_prometheus": os.getenv("ENABLE_PROMETHEUS_METRICS", "false").lower() == "true",
            "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090"))
        }
    }

    # Environment-specific overrides
    if env == "staging":
        config.update(_load_staging_config())
    elif env == "production":
        config.update(_load_production_config())

    return config

def _load_staging_config() -> Dict[str, Any]:
    """Load staging-specific configuration."""
    return {
        "app": {
            "debug": False,
            "cors_origins": ["https://staging.finbot.yourcompany.com"]
        },
        "logging": {
            "level": "WARNING"
        }
    }

def _load_production_config() -> Dict[str, Any]:
    """Load production-specific configuration."""
    return {
        "app": {
            "debug": False,
            "cors_origins": ["https://finbot.yourcompany.com"]
        },
        "logging": {
            "level": "ERROR"
        },
        "monitoring": {
            "enable_prometheus": True
        }
    }

# Global config instance
_config = None

def get_config() -> Dict[str, Any]:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
