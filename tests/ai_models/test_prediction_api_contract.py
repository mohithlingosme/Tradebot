"""Contract tests for the AIResponse schema."""

from __future__ import annotations

import pytest

from ai_models.pipeline import AIResponse


def test_ai_response_serializes_sources():
    response = AIResponse(type="answer", content="Hello", sources=["doc1", "doc2"])
    dump = response.model_dump()
    assert dump["sources"] == ["doc1", "doc2"]
    assert dump["type"] == "answer"


def test_ai_response_defaults_to_none_fields():
    response = AIResponse(type="needs_clarification", reason="more context needed")
    assert response.content is None
    assert response.sources is None
