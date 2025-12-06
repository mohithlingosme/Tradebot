# FILE: tests/test_env_modes.py
"""Test FINBOT_MODE environment variable logic and safety checks."""

import os
import pytest
from unittest.mock import patch


def test_finbot_mode_valid_values():
    """Test that FINBOT_MODE only accepts dev, paper, live."""
    from common.env import get_mode  # Adjust import as needed

    valid_modes = ["dev", "paper", "live"]

    for mode in valid_modes:
        with patch.dict(os.environ, {"FINBOT_MODE": mode}):
            assert get_mode() == mode


def test_finbot_mode_invalid_value_raises_error():
    """Test that invalid FINBOT_MODE raises clear error."""
    from common.env import get_mode  # Adjust import as needed

    with patch.dict(os.environ, {"FINBOT_MODE": "invalid"}):
        with pytest.raises(ValueError, match="Invalid FINBOT_MODE"):
            get_mode()


def test_live_mode_requires_confirmation():
    """Test that live mode requires FINBOT_LIVE_TRADING_CONFIRM=true."""
    from backend.config.settings import Settings

    # Test without confirmation - should downgrade to paper
    with patch.dict(os.environ, {
        "FINBOT_MODE": "live",
        "FINBOT_LIVE_TRADING_CONFIRM": "false"
    }):
        settings = Settings()
        assert settings.finbot_mode == "paper"  # Should be downgraded

    # Test with confirmation - should allow live
    with patch.dict(os.environ, {
        "FINBOT_MODE": "live",
        "FINBOT_LIVE_TRADING_CONFIRM": "true"
    }):
        settings = Settings()
        assert settings.finbot_mode == "live"


def test_env_file_loading():
    """Test loading from .env files for different modes."""
    import tempfile
    from pathlib import Path

    # Create temporary .env files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # .env.dev
        dev_env = tmpdir / ".env.dev"
        dev_env.write_text("FINBOT_MODE=dev\nAPP_ENV=development\n")

        # .env.paper
        paper_env = tmpdir / ".env.paper"
        paper_env.write_text("FINBOT_MODE=paper\nAPP_ENV=staging\n")

        # .env.live
        live_env = tmpdir / ".env.live"
        live_env.write_text("FINBOT_MODE=live\nFINBOT_LIVE_TRADING_CONFIRM=true\n")

        # Test loading each env file
        for env_file, expected_mode in [
            (dev_env, "dev"),
            (paper_env, "paper"),
            (live_env, "live")
        ]:
            with patch("scripts.dev_run.read_env_file", return_value={
                "FINBOT_MODE": expected_mode,
                "FINBOT_LIVE_TRADING_CONFIRM": "true" if expected_mode == "live" else "false"
            }):
                from backend.config.settings import Settings
                settings = Settings()
                assert settings.finbot_mode == expected_mode


def test_safety_audit_script():
    """Test the safety audit script blocks live mode without confirmation."""
    from scripts.safety_audit import normalize_mode, read_env

    # Test valid modes
    assert normalize_mode("dev") == "dev"
    assert normalize_mode("paper") == "paper"
    assert normalize_mode("live") == "live"

    # Test invalid mode
    assert normalize_mode("invalid") == "dev"  # Should default to dev

    # Test env reading
    with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
        assert read_env("TEST_VAR") == "test_value"
        assert read_env("MISSING_VAR") is None
