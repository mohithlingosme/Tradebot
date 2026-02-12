import pytest


def _skip(name: str, detail: str):
    pytest.skip(f"{name} not implemented: {detail} (see docs/testing/TEST_GAPS.md)")


@pytest.mark.e2e
def test_e2e_signup_login_mfa():
    _skip("e2e_signup_login_mfa", "frontend lacks MFA/signup pages for PaperPilot")


@pytest.mark.e2e
def test_e2e_create_project_upload_pdf():
    _skip("e2e_create_project_upload_pdf", "no project/upload flows in React frontend")


@pytest.mark.e2e
def test_e2e_import_url_build_library():
    _skip("e2e_import_url_build_library", "no library/import UI implemented")


@pytest.mark.e2e
def test_e2e_view_source_summary_and_highlights():
    _skip("e2e_view_source_summary_and_highlights", "no source summary/highlight UI")


@pytest.mark.e2e
def test_e2e_build_outline_generate_draft_with_citations():
    _skip("e2e_build_outline_generate_draft_with_citations", "no outline/draft/citation UI")


@pytest.mark.e2e
def test_e2e_switch_citation_style_and_regenerate_refs():
    _skip("e2e_switch_citation_style_and_regenerate_refs", "no citation style controls in UI")


@pytest.mark.e2e
def test_e2e_export_docx_pdf_download():
    _skip("e2e_export_docx_pdf_download", "no export/download UI flows")


@pytest.mark.e2e
def test_e2e_collaboration_invite_comment_approve():
    _skip("e2e_collaboration_invite_comment_approve", "no collaboration or commenting features")


@pytest.mark.e2e
def test_e2e_usage_credits_block_when_exhausted():
    _skip("e2e_usage_credits_block_when_exhausted", "no usage credit gating in frontend/backend")


@pytest.mark.e2e
def test_e2e_regression_recently_viewed_and_share_links():
    _skip("e2e_regression_recently_viewed_and_share_links", "no sharing/recently viewed implementation")
