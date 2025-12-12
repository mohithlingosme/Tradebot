"""
Technical Indicators Package

This package contains implementations of various technical indicators
used in trading strategies.

The package now exposes every indicator module under ``backend.indicators``,
so callers can continue using the convenient ``from backend.indicators import X``
syntax without manually importing submodules.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType
from typing import Dict, Iterable

from .indicator_catalog import (
    INDICATOR_LOOKUP,
    INDICATORS,
    IndicatorDefinition,
    get_indicator,
    indicators_by_category,
    search_indicators,
    top_indicators,
)
from .volume_indicators import VolumeIndicators

_CORE_EXPORTS = {
    "IndicatorDefinition": IndicatorDefinition,
    "INDICATORS": INDICATORS,
    "INDICATOR_LOOKUP": INDICATOR_LOOKUP,
    "get_indicator": get_indicator,
    "indicators_by_category": indicators_by_category,
    "search_indicators": search_indicators,
    "top_indicators": top_indicators,
    "VolumeIndicators": VolumeIndicators,
}

__all__ = list(_CORE_EXPORTS)
globals().update(_CORE_EXPORTS)

_EXCLUDED_MODULES = {
    "__init__",
    "indicator_catalog",
    "generate_indicator_stubs",
    "TODO_indicators",
    "utils",
    "volume_indicators",
}


def _module_exports(module: ModuleType) -> Dict[str, type]:
    """Return candidate classes for re-export from a module."""
    exports: Dict[str, type] = {}
    attr_names: Iterable[str]
    if hasattr(module, "__all__") and isinstance(module.__all__, (list, tuple)):
        attr_names = module.__all__  # type: ignore[assignment]
    else:
        attr_names = (
            name
            for name, value in vars(module).items()
            if inspect.isclass(value) and value.__module__ == module.__name__
        )
    for name in attr_names:
        value = getattr(module, name, None)
        if inspect.isclass(value):
            exports[name] = value
    return exports


def _discover_indicator_classes() -> Dict[str, type]:
    discovered: Dict[str, type] = {}
    for module_info in pkgutil.iter_modules(__path__):
        if module_info.name in _EXCLUDED_MODULES or module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{module_info.name}")
        for class_name, class_obj in _module_exports(module).items():
            # Later modules override earlier ones if names collide.
            discovered[class_name] = class_obj
    return discovered


_DYNAMIC_EXPORTS = _discover_indicator_classes()
globals().update(_DYNAMIC_EXPORTS)
__all__.extend(sorted(_DYNAMIC_EXPORTS))
__all__ = sorted(dict.fromkeys(__all__))
