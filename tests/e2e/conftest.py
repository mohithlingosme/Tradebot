import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_external_health_checks():
    """Autouse fixture to mock external network health checks used by API endpoints.

    Many endpoints call health-check helpers that perform network I/O; tests should be deterministic
    and not depend on external services during unit/E2E runs. This fixture patches `_hit_endpoint`
    to always return a small latency value.
    """
    with patch('backend.api.main._hit_endpoint', return_value=50.0) as _patch:
        yield _patch
