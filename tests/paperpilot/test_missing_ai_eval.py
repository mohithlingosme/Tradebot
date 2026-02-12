import pytest


def _skip(name: str, detail: str):
    pytest.skip(f"{name} not implemented: {detail} (see docs/testing/TEST_GAPS.md)")


@pytest.mark.ai_eval
def test_eval_summarization_faithfulness_set():
    _skip("eval_summarization_faithfulness_set", "no summarization model or eval dataset")


@pytest.mark.ai_eval
def test_eval_draft_citation_coverage_rate():
    _skip("eval_draft_citation_coverage_rate", "no drafting/citation generation pipeline")


@pytest.mark.ai_eval
def test_eval_claim_traceability_source_graph_score():
    _skip("eval_claim_traceability_source_graph_score", "no source graph to compute traceability")


@pytest.mark.ai_eval
def test_eval_hallucination_rate_strict_mode():
    _skip("eval_hallucination_rate_strict_mode", "no hallucination guardrails or strict mode implemented")


@pytest.mark.ai_eval
def test_eval_bluebook_format_accuracy_suite():
    _skip("eval_bluebook_format_accuracy_suite", "no citation formatting for Bluebook available")


@pytest.mark.ai_eval
def test_eval_regression_on_fixed_bug_prompts():
    _skip("eval_regression_on_fixed_bug_prompts", "no AI prompt/response regression harness")
