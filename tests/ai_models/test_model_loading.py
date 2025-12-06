"""Tests for FinbotAIPipeline prompt building and responses."""

from __future__ import annotations

import pytest

from ai_models.pipeline import FinbotAIPipeline
from ai_models.safety import SafetyVerdict


class DummySafety:
    def inspect_prompt(self, text: str) -> SafetyVerdict:
        return SafetyVerdict(True)

    def inspect_response(self, text: str, evidence):
        return SafetyVerdict(True, cleaned_text=text.strip())


class DummyRetriever:
    async def search(self, *_):
        return ["Finbot only trades what it understands."]


class DummyLLM:
    async def generate(self, prompt: str):
        return "Finbot answer"


@pytest.mark.asyncio
async def test_pipeline_answer_returns_clean_response():
    pipeline = FinbotAIPipeline(DummyLLM(), DummyRetriever(), DummySafety())
    response = await pipeline.answer(user_id="demo", question="What is Finbot?")
    assert response.type == "answer"
    assert "Finbot" in response.content


def test_build_prompt_includes_evidence():
    pipeline = FinbotAIPipeline(DummyLLM(), DummyRetriever(), DummySafety())
    prompt = pipeline._build_prompt("Q?", ["fact 1"])
    assert "fact 1" in prompt
    assert "Question:" in prompt
