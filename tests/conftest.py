import pytest
from _pytest.fixtures import FixtureDef


@pytest.fixture(autouse=True)
def ensure_fixturedef_unittest_attribute():
    """Ensure pytest_asyncio can reference FixtureDef.unittest without import errors."""
    if not hasattr(FixtureDef, "unittest"):
        setattr(FixtureDef, "unittest", False)
    yield
