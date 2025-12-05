"""Path helpers to avoid relative path bugs inside tests."""

from __future__ import annotations

from pathlib import Path

_UTILS_DIR = Path(__file__).resolve().parent
TESTS_ROOT = _UTILS_DIR.parent
REPO_ROOT = TESTS_ROOT.parent
BACKEND_ROOT = (REPO_ROOT / "backend").resolve()
SRC_ROOT = (REPO_ROOT / "src").resolve()


def repo_path(*parts: str) -> Path:
    """Return an absolute path under the repository root."""
    return (REPO_ROOT.joinpath(*parts)).resolve()


__all__ = [
    "BACKEND_ROOT",
    "REPO_ROOT",
    "SRC_ROOT",
    "TESTS_ROOT",
    "repo_path",
]

