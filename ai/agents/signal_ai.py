from __future__ import annotations

"""
Signal AI agent.

Produces structured, advisory-only signals in the LLMSignal schema.
It never issues executable orders or position sizes.
"""

import json
from typing import Any, Callable, Dict, Optional

from ai.schemas import LLMSignal


PromptRunner = Callable[..., Any]


class SignalAI:
    """Turns research + narratives into validated LLMSignal suggestions."""

    def __init__(self, llm_runner: PromptRunner):
        self.llm_runner = llm_runner

    def _default_signal(self, horizon: str, reason: str) -> LLMSignal:
        safe_horizon = horizon if horizon in {"intraday", "swing"} else "intraday"
        return LLMSignal(
            view="neutral",
            confidence=0.0,
            horizon=safe_horizon,
            stop_loss_hint="",
            target_hint="",
            reasoning=reason,
        )

    def generate_signal(
        self,
        symbol: str,
        horizon: str,
        research_summary: Optional[str] = None,
        narrative: Optional[str] = None,
        market_snapshot: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Produce an advisory-only LLMSignal plus metadata.
        """
        prompt = (
            "You are Signal AI. Provide a structured directional view only.\n"
            "Do NOT provide orders, sizes, leverage, or broker instructions.\n"
            "Return JSON matching this schema exactly:\n"
            '{"view": "long|short|neutral", "confidence": 0-1, "horizon": "intraday|swing", '
            '"stop_loss_hint": "text", "target_hint": "text", "reasoning": "text"}\n'
            f"Symbol: {symbol}\n"
            f"Horizon: {horizon}\n"
            f"Research summary: {research_summary or 'n/a'}\n"
            f"Narrative: {narrative or 'n/a'}\n"
            f"Market snapshot: {market_snapshot or 'n/a'}\n"
            "Stay concise. If uncertain, choose neutral with low confidence."
        )

        response = self.llm_runner(
            prompt=prompt,
            context={
                "role": "signal_ai",
                "data_type": "llm_signal",
                "symbol": symbol,
                "horizon": horizon,
                "format": "json",
                "expect_json": True,
            },
            max_tokens=180,
            temperature=0.25,
            expect_json=True,
        )

        meta = {
            "blocked": getattr(response, "blocked", False),
            "disclaimer": getattr(response, "disclaimer", None),
            "safety_findings": getattr(response, "safety_findings", []),
            "raw_text": getattr(response, "response", ""),
            "advisory_only": True,
        }

        if meta["blocked"]:
            meta["reason"] = "LLM output blocked by safety layer."
            return {"signal": self._default_signal(horizon, "blocked"), "meta": meta}

        try:
            parsed = json.loads(meta["raw_text"])
            llm_signal = LLMSignal.model_validate(parsed)
            return {"signal": llm_signal, "meta": meta}
        except Exception as exc:
            meta["reason"] = f"Failed to parse LLMSignal: {exc}"
            return {"signal": self._default_signal(horizon, "parse_error"), "meta": meta}
