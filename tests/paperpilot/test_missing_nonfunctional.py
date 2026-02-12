import pytest


def _skip(name: str, detail: str):
    pytest.skip(f"{name} not implemented: {detail} (see docs/testing/TEST_GAPS.md)")


@pytest.mark.load
def test_load_100_concurrent_pdf_uploads():
    _skip("load_100_concurrent_pdf_uploads", "no PDF upload endpoint or storage backend")


@pytest.mark.load
def test_load_50_concurrent_draft_generations():
    _skip("load_50_concurrent_draft_generations", "no drafting endpoint or LLM backend")


@pytest.mark.load
def test_load_vector_search_latency_p95_under_target():
    _skip("load_vector_search_latency_p95_under_target", "no vector search service to benchmark")


@pytest.mark.load
def test_load_export_large_doc_p95_under_target():
    _skip("load_export_large_doc_p95_under_target", "no export pipeline for documents")


@pytest.mark.load
def test_cost_per_1000_ai_calls_regression_guard():
    _skip("test_cost_per_1000_ai_calls_regression_guard", "no AI call metering implemented")


@pytest.mark.integration
def test_chaos_llm_timeout_retry_backoff():
    _skip("chaos_llm_timeout_retry_backoff", "no LLM client or retry policy to exercise")


@pytest.mark.integration
def test_chaos_vector_db_restart_recovery():
    _skip("chaos_vector_db_restart_recovery", "no vector database configured")


@pytest.mark.integration
def test_chaos_queue_worker_crash_resume():
    _skip("chaos_queue_worker_crash_resume", "no background queue/worker infrastructure in repo")


@pytest.mark.security
def test_sec_dast_auth_bypass_checks():
    _skip("sec_dast_auth_bypass_checks", "no authenticated endpoints beyond /auth to probe for bypass")


@pytest.mark.security
def test_sec_rbac_privilege_escalation_attempts():
    _skip("sec_rbac_privilege_escalation_attempts", "no RBAC enforcement layer implemented")


@pytest.mark.security
def test_sec_file_upload_malware_stub_scan():
    _skip("sec_file_upload_malware_stub_scan", "no file upload surface to scan")


@pytest.mark.security
def test_sec_data_export_and_delete_gdpr_like_flows():
    _skip("sec_data_export_and_delete_gdpr_like_flows", "no data export/delete endpoints")
