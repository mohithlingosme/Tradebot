import sys

from tests.utils.paths import BACKEND_ROOT

sys.path.insert(0, str(BACKEND_ROOT))

from core.ai_pipeline import AIPipeline, PromptRequest  # type: ignore
from core.safety import SafetyContext, SafetyFilter  # type: ignore


def test_safety_filter_blocks_overconfident_low_confidence_response():
    safety = SafetyFilter()
    context = SafetyContext(intent="market_analysis", confidence=0.3)

    result = safety.evaluate("This setup is guaranteed profit with zero risk.", context)

    assert result.blocked is True
    assert any(f.code == "overconfidence" for f in result.findings)
    assert result.disclaimer


def test_safety_filter_detects_unsafe_language():
    safety = SafetyFilter()

    result = safety.evaluate("You should kill yourself for losses.", SafetyContext(intent="general"))

    assert result.blocked is True
    assert any(f.code == "unsafe_content" for f in result.findings)
    assert "refused" in result.text.lower()


def test_process_prompt_propagates_disclaimer_in_mock_mode():
    pipeline = AIPipeline(api_key=None)
    request = PromptRequest(
        prompt="Share your trading view on NIFTY.",
        context={"data_type": "market_analysis", "confidence": 0.5},
        max_tokens=50,
    )

    response = pipeline.process_prompt(request)

    assert response.disclaimer is not None
    assert response.blocked is False
