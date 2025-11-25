"""Safety utilities for prompt/response inspection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence


JAILBREAK_PATTERNS = [
    re.compile(r"ignore\s+all\s+previous\s+instructions", re.I),
    re.compile(r"pretend\s+to\s+be", re.I),
]


@dataclass
class SafetyVerdict:
    allowed: bool
    reason: str | None = None
    cleaned_text: str | None = None


class SafetyLayer:
    """Simple regex-based safety guard with hallucination heuristics."""

    def __init__(self, moderation_client=None):
        self.moderation_client = moderation_client

    def inspect_prompt(self, text: str) -> SafetyVerdict:
        if any(pattern.search(text) for pattern in JAILBREAK_PATTERNS):
            return SafetyVerdict(False, "Prompt violates Finbot safety policy.")
        if self.moderation_client:
            moderation_verdict = self.moderation_client.moderate(text)
            if not moderation_verdict["allowed"]:
                return SafetyVerdict(False, "Prompt blocked by moderation provider.")
        return SafetyVerdict(True)

    def inspect_response(self, text: str, evidence: Sequence[str]) -> SafetyVerdict:
        if not evidence:
            return SafetyVerdict(False, "Insufficient grounding evidence.")
        hallucination_score = self._calc_grounding_score(text, evidence)
        if hallucination_score < 0.7:
            return SafetyVerdict(False, "Possible hallucination detected; requesting clarification.")
        if self.moderation_client:
            moderation_verdict = self.moderation_client.moderate(text)
            if not moderation_verdict["allowed"]:
                return SafetyVerdict(False, "Response blocked by moderation provider.")
        cleaned = text.strip()
        return SafetyVerdict(True, cleaned_text=cleaned)

    def _calc_grounding_score(self, response: str, evidence: Sequence[str]) -> float:
        response_tokens = set(response.lower().split())
        evidence_tokens = set(" ".join(evidence).lower().split())
        if not response_tokens:
            return 0.0
        overlap = response_tokens.intersection(evidence_tokens)
        return len(overlap) / len(response_tokens)
