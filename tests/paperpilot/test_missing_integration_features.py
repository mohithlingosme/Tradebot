import pytest


def _skip(name: str, detail: str):
    pytest.skip(f"{name} not implemented: {detail} (see docs/testing/TEST_GAPS.md)")


@pytest.mark.integration
def test_ingestion_to_embedding_pipeline_end_to_end():
    _skip("test_ingestion_to_embedding_pipeline_end_to_end", "no ingestion or embedding pipeline exists")


@pytest.mark.integration
def test_embedding_to_search_retrieval_quality_basic():
    _skip("test_embedding_to_search_retrieval_quality_basic", "no vector search/retrieval implementation")


@pytest.mark.integration
def test_draft_generation_with_citation_linking():
    _skip("test_draft_generation_with_citation_linking", "no drafting or citation linking modules")


@pytest.mark.integration
def test_plagiarism_check_integration_basic():
    _skip("test_plagiarism_check_integration_basic", "no plagiarism checking service")


@pytest.mark.integration
def test_export_pipeline_with_large_document():
    _skip("test_export_pipeline_with_large_document", "no export pipeline implemented")


@pytest.mark.integration
def test_provider_failover_llm_outage_fallback():
    _skip("test_provider_failover_llm_outage_fallback", "no AI provider abstraction or fallback logic")
