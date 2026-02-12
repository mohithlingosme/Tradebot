import { test } from '@playwright/test';

const skipReason = 'PaperPilot UI journeys are not implemented in this repository; see docs/testing/TEST_GAPS.md';

test.describe('PaperPilot E2E journeys', () => {
  test.skip(true, skipReason);

  test('e2e_signup_login_mfa', async () => {});
  test('e2e_create_project_upload_pdf', async () => {});
  test('e2e_import_url_build_library', async () => {});
  test('e2e_view_source_summary_and_highlights', async () => {});
  test('e2e_build_outline_generate_draft_with_citations', async () => {});
  test('e2e_switch_citation_style_and_regenerate_refs', async () => {});
  test('e2e_export_docx_pdf_download', async () => {});
  test('e2e_collaboration_invite_comment_approve', async () => {});
  test('e2e_usage_credits_block_when_exhausted', async () => {});
  test('e2e_regression_recently_viewed_and_share_links', async () => {});
});
