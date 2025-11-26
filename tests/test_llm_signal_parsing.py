import json

import pytest

from ai.agents.signal_ai import SignalAI
from ai.schemas import LLMSignal


def test_llm_signal_model_accepts_valid_payload():
    data = {
        "view": "long",
        "confidence": 0.8,
        "horizon": "intraday",
        "stop_loss_hint": "Below yesterday's low",
        "target_hint": "Near resistance",
        "reasoning": "Strong uptrend with volume.",
    }
    signal = LLMSignal(**data)
    assert signal.view == "long"
    assert signal.confidence == 0.8
    assert signal.horizon == "intraday"


def test_llm_signal_model_rejects_invalid_values():
    bad = {
        "view": "moon",
        "confidence": 1.5,
        "horizon": "weekly",
        "stop_loss_hint": "",
        "target_hint": "",
        "reasoning": "",
    }
    with pytest.raises(Exception):
        LLMSignal(**bad)


class _DummyLLMResponse:
    def __init__(self, text: str, blocked: bool = False):
        self.response = text
        self.blocked = blocked
        self.disclaimer = None
        self.safety_findings = []


def test_signal_ai_parses_json_and_handles_bad_output():
    def good_runner(**_kwargs):
        payload = {
            "view": "short",
            "confidence": 0.6,
            "horizon": "swing",
            "stop_loss_hint": "Above pivot",
            "target_hint": "Gap fill",
            "reasoning": "Momentum rolling over",
        }
        return _DummyLLMResponse(json.dumps(payload))

    ai = SignalAI(llm_runner=good_runner)
    result = ai.generate_signal(symbol="AAPL", horizon="swing")
    assert isinstance(result["signal"], LLMSignal)
    assert result["signal"].view == "short"

    def bad_runner(**_kwargs):
        return _DummyLLMResponse("not-json")

    result_bad = ai.generate_signal(symbol="AAPL", horizon="intraday", research_summary="")  # type: ignore[arg-type]
    ai_bad = SignalAI(llm_runner=bad_runner)
    fallback = ai_bad.generate_signal(symbol="AAPL", horizon="intraday")
    assert fallback["signal"].view == "neutral"
    assert fallback["signal"].confidence == 0.0
