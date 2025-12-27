# Backwards-compatible shim so existing imports continue to work.
from backend.app.core.config import settings  # noqa: F401

__all__ = ["settings"]
