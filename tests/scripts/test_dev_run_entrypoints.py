# FILE: tests/scripts/test_dev_run_entrypoints.py
"""Test python -m scripts.dev_run backend/ingestion/engine entrypoints (start & shutdown signals)."""

import pytest
from unittest.mock import patch, MagicMock, call
import subprocess
import signal
import time
import os


def test_dev_run_backend_entrypoint():
    """Test dev_run script can start backend service."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config:

        mock_config.return_value = {"port": 8000, "host": "localhost"}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        # Mock command line args for backend
        with patch("sys.argv", ["dev_run.py", "backend"]):
            result = main()

        # Should call uvicorn or similar
        mock_run.assert_called()
        args, kwargs = mock_run.call_args
        command = args[0]
        assert "uvicorn" in " ".join(command) or "backend" in " ".join(command)


def test_dev_run_ingestion_entrypoint():
    """Test dev_run script can start ingestion service."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config:

        mock_config.return_value = {"port": 8001, "host": "localhost"}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "ingestion"]):
            result = main()

        mock_run.assert_called()
        args, kwargs = mock_run.call_args
        command = args[0]
        assert "ingestion" in " ".join(command)


def test_dev_run_engine_entrypoint():
    """Test dev_run script can start trading engine."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config:

        mock_config.return_value = {"port": 8002, "host": "localhost"}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "engine"]):
            result = main()

        mock_run.assert_called()
        args, kwargs = mock_run.call_args
        command = args[0]
        assert "engine" in " ".join(command) or "trading" in " ".join(command)


def test_dev_run_invalid_service():
    """Test dev_run script rejects invalid service names."""
    from scripts.dev_run import main

    with patch("sys.argv", ["dev_run.py", "invalid_service"]):
        with pytest.raises(SystemExit):
            main()


def test_dev_run_with_config_file():
    """Test dev_run script accepts custom config file."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("os.path.exists") as mock_exists:

        mock_exists.return_value = True
        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "--config", "custom_config.yaml"]):
            main()

        # Should load custom config
        mock_config.assert_called_with("custom_config.yaml")


def test_dev_run_environment_variables():
    """Test dev_run script passes environment variables."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch.dict(os.environ, {"FINBOT_MODE": "dev", "DATABASE_URL": "sqlite:///test.db"}):

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend"]):
            main()

        # Should pass environment variables
        args, kwargs = mock_run.call_args
        assert "env" in kwargs
        env_vars = kwargs["env"]
        assert env_vars["FINBOT_MODE"] == "dev"
        assert env_vars["DATABASE_URL"] == "sqlite:///test.db"


def test_dev_run_shutdown_signal_handling():
    """Test dev_run script handles shutdown signals gracefully."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("signal.signal") as mock_signal:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend"]):
            main()

        # Should register signal handlers
        mock_signal.assert_any_call(signal.SIGINT, pytest.any)
        mock_signal.assert_any_call(signal.SIGTERM, pytest.any)


def test_dev_run_process_monitoring():
    """Test dev_run script monitors subprocess and handles failures."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 1  # Failure
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend"]):
            with pytest.raises(SystemExit):
                main()


def test_dev_run_log_file_output():
    """Test dev_run script redirects logs to files."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "--log-file", "backend.log"]):
            main()

        # Should redirect stdout/stderr to log file
        args, kwargs = mock_run.call_args
        assert "stdout" in kwargs
        assert "stderr" in kwargs


def test_dev_run_multiple_services():
    """Test dev_run script can start multiple services."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("multiprocessing.Process") as mock_process_class:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "ingestion", "--parallel"]):
            main()

        # Should create processes for each service
        assert mock_process_class.call_count >= 2


def test_dev_run_dependency_check():
    """Test dev_run script checks for service dependencies."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("scripts.dev_run.check_dependencies") as mock_check:

        mock_config.return_value = {"port": 8000}
        mock_check.return_value = True  # Dependencies OK
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend"]):
            main()

        mock_check.assert_called()


def test_dev_run_dependency_failure():
    """Test dev_run script fails when dependencies are missing."""
    with patch("scripts.dev_run.check_dependencies") as mock_check:
        mock_check.return_value = False  # Dependencies missing

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend"]):
            with pytest.raises(SystemExit):
                main()


def test_dev_run_health_check():
    """Test dev_run script performs health checks on started services."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("scripts.dev_run.wait_for_service") as mock_wait, \
         patch("time.sleep") as mock_sleep:

        mock_config.return_value = {"port": 8000}
        mock_wait.return_value = True  # Service healthy
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "--wait-for-healthy"]):
            main()

        mock_wait.assert_called_with("localhost", 8000)


def test_dev_run_health_check_timeout():
    """Test dev_run script handles health check timeouts."""
    with patch("scripts.dev_run.wait_for_service") as mock_wait:
        mock_wait.return_value = False  # Service never healthy

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "--wait-for-healthy", "--timeout", "30"]):
            with pytest.raises(SystemExit):
                main()


def test_dev_run_reload_on_file_change():
    """Test dev_run script can reload services on file changes."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("watchdog.observers.Observer") as mock_observer:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "--reload"]):
            main()

        # Should set up file watcher
        mock_observer.assert_called()


def test_dev_run_debug_mode():
    """Test dev_run script enables debug mode."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "--debug"]):
            main()

        # Should pass debug environment variable
        args, kwargs = mock_run.call_args
        assert "env" in kwargs
        env_vars = kwargs["env"]
        assert env_vars.get("DEBUG") == "true"


def test_dev_run_profile_mode():
    """Test dev_run script enables profiling."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("cProfile.Profile") as mock_profile:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "--profile"]):
            main()

        # Should enable profiling
        mock_profile.assert_called()


def test_dev_run_with_custom_python_path():
    """Test dev_run script accepts custom Python path."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend", "--python-path", "/custom/python"]):
            main()

        # Should use custom Python executable
        args, kwargs = mock_run.call_args
        command = args[0]
        assert "/custom/python" in command[0]


def test_dev_run_service_discovery():
    """Test dev_run script registers services for discovery."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("scripts.dev_run.register_service") as mock_register:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend"]):
            main()

        # Should register service
        mock_register.assert_called_with("backend", "localhost", 8000)


def test_dev_run_cleanup_on_exit():
    """Test dev_run script cleans up resources on exit."""
    with patch("subprocess.run") as mock_run, \
         patch("scripts.dev_run.load_config") as mock_config, \
         patch("scripts.dev_run.cleanup_resources") as mock_cleanup:

        mock_config.return_value = {"port": 8000}
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        from scripts.dev_run import main

        with patch("sys.argv", ["dev_run.py", "backend"]):
            try:
                main()
            finally:
                # Should cleanup even on normal exit
                mock_cleanup.assert_called()
