"""Helpers for expanding ${VAR_NAME} patterns across configuration data."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Iterable

_ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::-(.*?))?\}")
_VALID_MODES = ("dev", "paper", "live")


def _expand_str(value: str) -> str:
    """Expand ${VAR} or ${VAR:-default} inside a string."""

    def replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default_value = match.group(2)
        env_value = os.getenv(var_name)
        if env_value not in (None, ""):
            return env_value
        if default_value is not None:
            return default_value
        return match.group(0)

    return _ENV_PATTERN.sub(replace, value)


def expand_env_vars(value: Any) -> Any:
    """Recursively expand environment placeholders within nested data structures."""

    if isinstance(value, dict):
        return {key: expand_env_vars(val) for key, val in value.items()}
    if isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    if isinstance(value, tuple):
        return tuple(expand_env_vars(item) for item in value)
    if isinstance(value, set):  # pragma: no cover - rarely used but supported
        return {expand_env_vars(item) for item in value}
    if isinstance(value, Path):
        return Path(_expand_str(str(value)))
    if isinstance(value, str):
        return _expand_str(value)
    return value


def get_mode(default: str = "dev", *, allowed: Iterable[str] = _VALID_MODES) -> str:
    """
    Return the normalized FINBOT_MODE value while enforcing allowed options.

    Args:
        default: Mode to fall back to when FINBOT_MODE is unset.
        allowed: Collection of permitted modes (case-insensitive).
    """
    raw_value = os.getenv("FINBOT_MODE", default)
    normalized = raw_value.strip().lower()
    allowed_set = {mode.lower() for mode in allowed}
    if normalized not in allowed_set:
        raise ValueError(
            f"Invalid FINBOT_MODE='{raw_value}'. Expected one of: {', '.join(sorted(allowed_set))}."
        )
    return normalized


__all__ = ["expand_env_vars", "get_mode"]
