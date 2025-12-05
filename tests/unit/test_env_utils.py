"""Tests for shared environment placeholder expansion helpers."""

from pathlib import Path

from common.env import expand_env_vars


def test_expand_env_vars_replaces_nested_placeholders(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "super-secret")
    config = {"providers": {"alpha": {"token": "${API_TOKEN}"}}}

    expanded = expand_env_vars(config)

    assert expanded["providers"]["alpha"]["token"] == "super-secret"


def test_expand_env_vars_supports_default(monkeypatch):
    monkeypatch.delenv("MISSING_VALUE", raising=False)

    assert expand_env_vars("${MISSING_VALUE:-fallback}") == "fallback"


def test_expand_env_vars_preserves_placeholder_when_missing(monkeypatch):
    monkeypatch.delenv("UNSET_VALUE", raising=False)

    original = "api-key-${UNSET_VALUE}"
    assert expand_env_vars(original) == original


def test_expand_env_vars_handles_path_objects(monkeypatch):
    monkeypatch.setenv("LOG_DIR", "/tmp/finbot")
    original = Path("${LOG_DIR}/finbot.log")

    resolved = expand_env_vars(original)

    assert isinstance(resolved, Path)
    assert str(resolved) == "/tmp/finbot/finbot.log"
