# Test Gaps and Missing Features

The requested PaperPilot functionality (workspaces, PDF uploads, vector search, drafting/citations, billing, MFA, etc.) is not present in this Finbot codebase. Tests covering these areas are marked with `pytest.skip` and should be re-enabled when the features land.

## Backend/Auth
- `test_auth_mfa_enable_disable`, `test_auth_password_reset_flow`, `test_auth_session_refresh_and_expiry` (partial), `test_csrf_protection_if_applicable`: MFA, password reset, CSRF/session refresh endpoints do not exist (`backend/app/api/routes/` only exposes basic auth profile/password change).

## RBAC/Org
- `test_rbac_role_matrix_viewer_editor_admin`, `test_rbac_project_level_permissions`, `test_rbac_shared_library_permissions`, `test_org_invite_accept_revoke`, `test_member_role_change_audit_log`, `test_file_storage_access_scoped`: no RBAC middleware or org/workspace models beyond a simple `User.role` enum.

## Content Ingestion
- `test_upload_pdf_success`, `test_upload_pdf_reject_invalid_mime`, `test_upload_max_size_limits`, `test_source_metadata_extraction`, `test_source_dedup_by_hash`, `test_source_versioning`, `test_url_import_*`, `test_ocr_*`, `test_chunking_*`, `test_embedding_*`, `test_vector_*`: the backend has no upload/ingestion/vector DB routes or services; search across `backend/` and `ingestion/` shows no HTTP handlers for these features.

## Summaries/Outline/Drafts/Citations
- `test_summarize_*`, `test_outline_*`, `test_draft_*`, `test_citation_*`, `test_source_graph_*`, `test_strict_mode_refuses_uncited_statements`, `test_citation_misattribution_detection`, `test_editor_*`, `test_export_*`, `test_notification_on_export_complete`: no summarization/LLM/citation/export modules or endpoints in the backend or frontend.

## Billing/Usage/Security
- `test_billing_*`, `test_usage_*`, `test_audit_log_records_sensitive_actions`, `test_event_tracking_schema_validation`, `test_rate_limit_enforced`, `test_encryption_flags_and_key_rotation_hooks`: no billing state machine, usage metering, audit log, or encryption hooks implemented.

## Integration Flows
- `test_ingestion_to_embedding_pipeline_end_to_end`, `test_embedding_to_search_retrieval_quality_basic`, `test_draft_generation_with_citation_linking`, `test_plagiarism_check_integration_basic`, `test_export_pipeline_with_large_document`, `test_provider_failover_llm_outage_fallback`: dependent pipeline stages absent.

## API Contract
- `test_api_openapi_schema_no_breaking_changes`, `test_api_pagination_consistency_sources`, `test_api_filter_sort_search_consistency`, `test_api_permissions_on_each_endpoint`: no OpenAPI spec or route coverage for the PaperPilot endpoints; backend/app/main.py only exposes `/health` and auth is partially wired.

## E2E UI
- `e2e_*` journeys: React frontend (`frontend/`) implements trading dashboards, not PaperPilot UI; there are no pages for upload/workspaces/citations.

## Load/Reliability/Security
- `load_100_concurrent_pdf_uploads`, `load_50_concurrent_draft_generations`, `load_vector_search_latency_p95_under_target`, `load_export_large_doc_p95_under_target`, `test_cost_per_1000_ai_calls_regression_guard`, `chaos_*`, `sec_dast_auth_bypass_checks`, `sec_rbac_privilege_escalation_attempts`, `sec_file_upload_malware_stub_scan`, `sec_data_export_and_delete_gdpr_like_flows`: underlying endpoints do not exist; scripts are stubbed to skip until implemented.

## AI Eval
- `eval_*` suites: no AI pipeline, prompt sets, or evaluators are present; harness tests are skipped until an AI module is added.
