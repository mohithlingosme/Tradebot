"""AI pipeline for Finbot responses with safety controls."""

from __future__ import annotations

from typing import Sequence

from pydantic import BaseModel


class AIResponse(BaseModel):
    """Structured AI response."""

    type: str
    content: str | None = None
    reason: str | None = None
    sources: Sequence[str] | None = None


class FinbotAIPipeline:
    """Simple orchestrator that performs retrieval, LLM call, and safety checks."""

    def __init__(self, llm_client, retriever, safety_layer):
        self.llm_client = llm_client
        self.retriever = retriever
        self.safety_layer = safety_layer

    async def answer(self, user_id: str, question: str) -> AIResponse:
        prompt_verdict = self.safety_layer.inspect_prompt(question)
        if not prompt_verdict.allowed:
            return AIResponse(type="blocked", reason=prompt_verdict.reason)

        evidence = await self.retriever.search(question)
        prompt = self._build_prompt(question, evidence)

        llm_output = await self.llm_client.generate(prompt)
        response_verdict = self.safety_layer.inspect_response(llm_output, evidence)
        if not response_verdict.allowed:
            return AIResponse(type="needs_clarification", reason=response_verdict.reason)

        return AIResponse(type="answer", content=response_verdict.cleaned_text, sources=list(evidence))

    def _build_prompt(self, question: str, evidence: Sequence[str]) -> str:
        evidence_text = "\n".join(f"- {item}" for item in evidence)
        return f"""You are Finbot, a factual finance assistant.
Ground your answer strictly on the evidence below. If insufficient, reply with "I need more information."

Evidence:
{evidence_text or 'No evidence'}

Question: {question}
"""
