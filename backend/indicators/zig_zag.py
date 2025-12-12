"""
Compatibility shim for the Zig Zag indicator.

Some callers prefer importing :mod:`backend.indicators.zig_zag` to match the
spelling in Indicator.txt.  The real implementation lives in
``backend.indicators.zigzag``; this module simply re-exports the same class.
"""

from __future__ import annotations

from .zigzag import ZigZag

__all__ = ["ZigZag"]
