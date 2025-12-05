"""
Configuration management for market data ingestion.
"""

from pathlib import Path
from typing import Any, Dict

import yaml
from common.env import expand_env_vars


def load_config(config_path: str = "market_data/config/default.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable substitution.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Substitute environment variables
    _substitute_env_vars(config)

    return config


def _substitute_env_vars(data: Any) -> Any:
    """Recursively substitute environment variables in configuration data."""

    return expand_env_vars(data)
