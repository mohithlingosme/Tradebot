"""
Service helpers for orchestrating dynamic indicator calculations.

The project exposes dozens of indicator modules under backend/indicators.  This
utility walks those modules, instantiates each indicator class, and executes the
`calculate_series` method when possible so higher level endpoints can return a
complete indicator dictionary without manually wiring every module.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import math
import pkgutil
import re
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

INDICATOR_PACKAGE = "backend.indicators"
INDICATOR_ROOT = Path(__file__).resolve().parent / "indicators"

EXCLUDED_MODULES = {
    "__init__",
    "generate_indicator_stubs",
    "indicator_catalog",
    "TODO_indicators",
    "volume_indicators",
    "utils",
}

COLUMN_ALIASES = {
    "open": "open",
    "opens": "open",
    "high": "high",
    "highs": "high",
    "low": "low",
    "lows": "low",
    "close": "close",
    "closes": "close",
    "price": "close",
    "prices": "close",
    "series": "close",
    "values": "close",
    "volume": "volume",
    "volumes": "volume",
    "timestamp": "time",
    "timestamps": "time",
    "time": "time",
    "times": "time",
}

COLOR_SAFE_TYPES = (int, float, str, bool, type(None))


def calculate_all_indicators(df: pd.DataFrame) -> Dict[str, List[Optional[float]]]:
    """
    Iterate over every indicator module, execute the calculation, and return a
    dictionary keyed by indicator slug.  Errors in individual modules are logged
    but do not abort the full run.
    """
    indicators: Dict[str, List[Optional[float]]] = {}
    for module_info in pkgutil.iter_modules([str(INDICATOR_ROOT)]):
        if module_info.name in EXCLUDED_MODULES or module_info.name.startswith("_"):
            continue
        module_name = f"{INDICATOR_PACKAGE}.{module_info.name}"
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            logger.debug("Skipping module %s due to import error: %s", module_name, exc)
            continue

        for indicator_class in _discover_indicator_classes(module):
            indicator_key = _indicator_key(module_info.name, indicator_class.__name__)
            if indicator_key in indicators:
                continue
            try:
                instance = indicator_class()
            except Exception as exc:
                logger.debug(
                    "Unable to instantiate %s from %s: %s", indicator_class.__name__, module_name, exc
                )
                continue

            calculate_series = getattr(instance, "calculate_series", None)
            if not callable(calculate_series):
                continue

            signature = inspect.signature(calculate_series)
            arguments = _prepare_arguments(signature, df)
            if arguments is None:
                continue

            try:
                series = calculate_series(*arguments)
            except Exception as exc:
                logger.debug(
                    "Indicator %s failed during execution: %s", indicator_class.__name__, exc
                )
                continue

            normalized = _normalize_series(series)
            if not normalized:
                continue
            indicators[indicator_key] = normalized
    return indicators


def _discover_indicator_classes(module: Any) -> Iterable[type]:
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ != module.__name__:
            continue
        if obj.__name__.startswith("_"):
            continue
        if not hasattr(obj, "calculate_series"):
            continue
        # Allow both dataclasses and regular classes.
        if is_dataclass(obj) or True:
            yield obj


def _indicator_key(module_name: str, class_name: str) -> str:
    candidate = class_name if class_name else module_name
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", candidate).lower()
    if snake.startswith("indicator_"):
        snake = snake[len("indicator_") :]
    return snake or module_name


def _prepare_arguments(signature: inspect.Signature, df: pd.DataFrame) -> Optional[List[Any]]:
    arguments: List[Any] = []
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        column_name = COLUMN_ALIASES.get(name.lower())
        if column_name is None:
            return None
        if column_name not in df.columns:
            return None
        if column_name == "time":
            arguments.append(df[column_name].tolist())
        else:
            arguments.append(df[column_name].astype(float).tolist())
    return arguments


def _normalize_series(series: Any) -> List[Optional[float]]:
    data: List[Any]
    if series is None:
        return []
    if isinstance(series, pd.DataFrame):
        # Too complex to plot consistently.
        return []
    if isinstance(series, pd.Series):
        data = series.tolist()
    elif isinstance(series, np.ndarray):
        data = series.tolist()
    elif isinstance(series, (list, tuple)):
        data = list(series)
    else:
        data = [series]

    normalized: List[Optional[float]] = []
    for item in data:
        normalized.append(_serialize_value(item))
    if all(value is None for value in normalized):
        return []
    return normalized


def _serialize_value(value: Any) -> Optional[float]:
    if isinstance(value, COLOR_SAFE_TYPES):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        # Non-numeric scalars (strings/bools) cannot be charted meaningfully.
        return None
    if isinstance(value, dict):
        return None
    if isinstance(value, (list, tuple)):
        return None
    if hasattr(value, "item"):
        try:
            scalar = value.item()
            return _serialize_value(scalar)
        except Exception:
            return None
    return None


__all__ = ["calculate_all_indicators"]
