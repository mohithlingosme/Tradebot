import pytest


def _skip(name: str, detail: str):
    pytest.skip(f"{name} not implemented: {detail} (see docs/testing/TEST_GAPS.md)")


@pytest.mark.api
def test_api_openapi_schema_no_breaking_changes():
    _skip("test_api_openapi_schema_no_breaking_changes", "no OpenAPI schema or router registration in backend/app/main.py")


@pytest.mark.api
def test_api_pagination_consistency_sources():
    _skip("test_api_pagination_consistency_sources", "no sources endpoint with pagination")


@pytest.mark.api
def test_api_filter_sort_search_consistency():
    _skip("test_api_filter_sort_search_consistency", "no searchable resources implemented")


@pytest.mark.api
def test_api_errors_standard_format():
    _skip("test_api_errors_standard_format", "no standardized error envelope to validate")


@pytest.mark.api
def test_api_permissions_on_each_endpoint():
    _skip("test_api_permissions_on_each_endpoint", "auth dependencies not applied across routes")
