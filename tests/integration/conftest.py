import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_external_health_checks_integration():
    """Patch external health check network calls in integration tests to avoid flaky network calls."""
    with patch('backend.api.main._hit_endpoint', return_value=50.0):
        yield
