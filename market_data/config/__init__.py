"""
Configuration management for market data ingestion.
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml


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
    """
    Recursively substitute environment variables in configuration data.

    Args:
        data: Configuration data (dict, list, or primitive)
    """
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = _substitute_env_vars(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = _substitute_env_vars(item)
    elif isinstance(data, str):
        # Check if string contains environment variable pattern ${VAR_NAME}
        if '${' in data and '}' in data:
            return _expand_env_vars(data)

    return data


def _expand_env_vars(value: str) -> str:
    """
    Expand environment variables in a string.

    Args:
        value: String that may contain ${VAR_NAME} patterns

    Returns:
        String with environment variables expanded
    """
    import re

    def replace_var(match):
        var_name = match.group(1)
        env_value = os.getenv(var_name)
        if env_value is None:
            raise ValueError(f"Environment variable {var_name} is not set")
        return env_value

    # Replace ${VAR_NAME} patterns
    return re.sub(r'\$\{([^}]+)\}', replace_var, value)
