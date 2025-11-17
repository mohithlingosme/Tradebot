"""
Safety and hallucination reduction utilities for the AI pipeline.
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_FINANCIAL_DISCLAIMER = (
    os.getenv(
        "FINBOT_FINANCIAL_DISCLAIMER",
        "Finbot responses are for informational purposes only and do not constitute financial advice. "
        "Please consult a registered adviser before making investment decisions.",
    )
)


@dataclass
class SafetyFinding:
    """Finding detected by the safety layer."""

    code: str
    message: str
    severity: str = "warning"

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


@dataclass
class SafetyContext:
    """Metadata passed to the safety filter."""

    intent: str = "general"
    confidence: Optional[float] = None
    expect_json: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def normalized_confidence(self, default: float = 0.75) -> float:
        """Clamp confidence into [0, 1] with fallbacks."""
        if self.confidence is None:
            quality = (self.metadata or {}).get("data_quality")
            if quality == "low":
                return 0.35
            if quality == "high":
                return 0.9
            return default
        try:
            value = float(self.confidence)
        except (TypeError, ValueError):
            return default
        return max(0.0, min(1.0, value))


@dataclass
class SafetyResult:
    """Safety verdict for a model response."""

    text: str
    findings: List[SafetyFinding] = field(default_factory=list)
    disclaimer: Optional[str] = None
    blocked: bool = False
    confidence: Optional[float] = None


class SafetyFilter:
    """Composable guardrails for AI responses."""

    FINANCIAL_INTENTS = {
        "market_analysis",
        "portfolio_analysis",
        "trading_plan",
        "paper_trading",
        "financial_advice",
        "portfolio_optimizer",
        "research_brief",
        "decision_analysis",
    }

    OVERCONFIDENT_TERMS = [
        "guaranteed",
        "definitely",
        "certainly",
        "will double",
        "zero risk",
        "risk-free",
        "cannot fail",
        "100% sure",
    ]

    UNSAFE_KEYWORDS = [
        "kill yourself",
        "suicide",
        "bomb",
        "weapon",
        "terror",
        "hate speech",
        "self-harm",
        "extremist",
    ]

    def __init__(self, financial_disclaimer: Optional[str] = None):
        self.financial_disclaimer = financial_disclaimer or DEFAULT_FINANCIAL_DISCLAIMER
        self.low_confidence_threshold = 0.65
        self.block_confidence_threshold = 0.4

    def evaluate(self, text: str, context: Optional[SafetyContext] = None) -> SafetyResult:
        """Apply safety policies to a model response."""
        context = context or SafetyContext()
        sanitized = (text or "").strip()
        result = SafetyResult(
            text=sanitized if sanitized else "No reliable response was generated.",
            confidence=context.normalized_confidence(),
        )

        if not sanitized:
            result.blocked = True
            result.findings.append(
                SafetyFinding(
                    code="empty_response",
                    message="The model returned an empty response.",
                    severity="error",
                )
            )
            return self._add_disclaimer_if_needed(result, context)

        if self._contains_unsafe_content(sanitized):
            result.blocked = True
            result.text = (
                "The assistant refused to answer because the request triggered "
                "internal safety policies."
            )
            result.findings.append(
                SafetyFinding(
                    code="unsafe_content",
                    message="Potentially unsafe or disallowed content detected.",
                    severity="critical",
                )
            )
            return self._add_disclaimer_if_needed(result, context)

        overconfident = self._has_overconfident_language(sanitized)
        if overconfident and result.confidence < self.low_confidence_threshold:
            result.findings.append(
                SafetyFinding(
                    code="overconfidence",
                    message="Overconfident tone detected while data confidence is low.",
                    severity="warning",
                )
            )
            if result.confidence < self.block_confidence_threshold:
                result.blocked = True
                result.text = (
                    "The assistant withheld a response because the available data "
                    "did not meet confidence requirements."
                )
            elif not context.expect_json:
                result.text = self._prepend_notice(
                    "Caution: Data confidence is limited; independently verify before acting.",
                    result.text,
                )

        if self._looks_nonsensical(sanitized):
            result.blocked = True
            result.text = (
                "The assistant detected potential hallucinations and refused to provide the response."
            )
            result.findings.append(
                SafetyFinding(
                    code="hallucination",
                    message="Response appears nonsensical or low-quality.",
                    severity="error",
                )
            )

        return self._add_disclaimer_if_needed(result, context)

    def _add_disclaimer_if_needed(self, result: SafetyResult, context: SafetyContext) -> SafetyResult:
        """Attach financial disclaimer when intent requires it."""
        if context.intent in self.FINANCIAL_INTENTS or context.metadata.get("requires_disclaimer"):
            result.disclaimer = self.financial_disclaimer
        return result

    def _has_overconfident_language(self, text: str) -> bool:
        candidate = text.lower()
        return any(term in candidate for term in self.OVERCONFIDENT_TERMS)

    def _contains_unsafe_content(self, text: str) -> bool:
        candidate = text.lower()
        return any(keyword in candidate for keyword in self.UNSAFE_KEYWORDS)

    def _looks_nonsensical(self, text: str) -> bool:
        alnum_chars = sum(ch.isalnum() for ch in text)
        proportion = alnum_chars / max(len(text), 1)
        repeated = bool(re.search(r"(.)\1{4,}", text))
        gibberish_tokens = re.findall(r"[#@]{3,}", text)
        return proportion < 0.35 or repeated or bool(gibberish_tokens)

    def _prepend_notice(self, notice: str, text: str) -> str:
        if text.lower().startswith("caution:") or text.lower().startswith("note:"):
            return text
        return f"{notice}\n\n{text}"


# Shared filter instance for reuse
safety_filter = SafetyFilter()
