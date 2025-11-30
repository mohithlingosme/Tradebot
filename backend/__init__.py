"""
Finbot Backend Package

This package contains the core backend modules for the Finbot autonomous trading system.

It also ships a tiny compatibility shim so the FastAPI/Starlette TestClient keeps working
even when `httpx` is newer (>=0.28) and no longer accepts the legacy `app=` argument.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

import httpx

__version__ = "0.1.0"
__author__ = "Finbot Team"


def _patch_httpx_testclient() -> None:
    """
    Starlette's TestClient still passes `app=` to httpx.Client, which 0.28+ rejects.
    In local/dev environments where a newer httpx is installed, tests would crash
    before even hitting our code. Patch the Client __init__ to translate `app` into
    an ASGITransport so TestClient can function across httpx versions.
    """

    # If the signature already accepts `app`, there's nothing to do.
    try:
        sig = inspect.signature(httpx.Client.__init__)
    except Exception:
        return
    if "app" in sig.parameters:
        return

    # Avoid double-patching.
    if getattr(httpx.Client, "_finbot_accepts_app", False):
        return

    original_init: Callable[..., Any] = httpx.Client.__init__

    def patched_init(
        self,
        *args: Any,
        app: Any = None,
        transport: httpx.BaseTransport | None = None,
        **kwargs: Any,
    ) -> None:
        if app is not None and transport is None:
            try:
                transport = httpx.ASGITransport(app=app)
            except Exception:
                # Fall back to whatever transport the caller provided; let httpx raise.
                pass
        return original_init(self, *args, transport=transport, **kwargs)

    httpx.Client.__init__ = patched_init  # type: ignore[assignment]
    httpx.Client._finbot_accepts_app = True  # type: ignore[attr-defined]


_patch_httpx_testclient()
