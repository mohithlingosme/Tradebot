import httpx
import pytest
from _pytest.fixtures import FixtureDef

_HTTPX_CLIENT_INIT = httpx.Client.__init__


def _compatible_httpx_client_init(self, *args, **kwargs):
    """Allow Starlette's TestClient to run with httpx >=0.28."""
    kwargs.pop("app", None)
    return _HTTPX_CLIENT_INIT(self, *args, **kwargs)


httpx.Client.__init__ = _compatible_httpx_client_init


@pytest.fixture(autouse=True)
def ensure_fixturedef_unittest_attribute():
    """Ensure pytest_asyncio can reference FixtureDef.unittest without import errors."""
    if not hasattr(FixtureDef, "unittest"):
        setattr(FixtureDef, "unittest", False)
    yield
