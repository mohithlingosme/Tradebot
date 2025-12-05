import os
import tempfile
from pathlib import Path
import pytest

from backend.app.managers.logging_manager import LoggingManager, LogAccessError
from backend.app.config import settings


def test_read_logs_raises_when_missing(monkeypatch, tmp_path):
    # Ensure settings.log_file points to a missing file
    missing_path = tmp_path / "no-such-log.log"
    monkeypatch.setattr(settings, "log_file", str(missing_path))
    monkeypatch.setattr(settings, "log_dir", str(missing_path.parent))

    manager = LoggingManager()
    with pytest.raises(LogAccessError):
        # Use internal method with a small limit/since/until
        manager._read_logs(level="INFO", limit=10, since=None, until=None)


def test_read_logs_raises_when_unreadable(monkeypatch, tmp_path):
    # Create an unreadable file by monkeypatching Path.open to raise OSError
    test_file = tmp_path / "test.log"
    test_file.write_text("2023-01-01 10:00:00,000 - app - INFO - [system] start")
    monkeypatch.setattr(settings, "log_file", str(test_file))
    monkeypatch.setattr(settings, "log_dir", str(test_file.parent))

    class FakePath(type(Path("."))):
        pass

    # Monkeypatch Path.open for this specific log path
    original_open = Path.open

    def fake_open(self, *args, **kwargs):
        if str(self) == str(test_file):
            raise OSError("permission denied")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fake_open)
    manager = LoggingManager()
    try:
        with pytest.raises(LogAccessError):
            manager._read_logs(level="INFO", limit=10, since=None, until=None)
    finally:
        # Cleanup monkeypatch to avoid impacting other tests
        monkeypatch.setattr(Path, "open", original_open)
