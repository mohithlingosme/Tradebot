from __future__ import annotations

"""
Narrative AI agent.

Produces human-readable narratives of market conditions and themes.
It does not emit trading instructions or executable orders.
"""

from typing import Any, Callable, Dict, Optional

from ai.agents.research_ai import ResearchAI


PromptRunner = Callable[..., Any]


class NarrativeAI:
    """Transforms research outputs into market narratives without directives."""

    def __init__(self, research_ai: ResearchAI, llm_runner: PromptRunner):
        self.research_ai = research_ai
        self.llm_runner = llm_runner

    def market_narrative(self, index: str, horizon: str, research_summary: Optional[str] = None) -> str:
        """
        Generate a market-wide narrative (no trade instructions).
        """
        summary = research_summary or self.research_ai.summarize_news([index])
        prompt = (
            "You are Narrative AI. Explain current market tone without giving orders.\n"
            f"Index: {index}\n"
            f"Horizon: {horizon}\n"
            f"Research summary: {summary}\n"
            "Describe key drivers, risks, and what could shift the view. Avoid directives."
        )
        response = self.llm_runner(
            prompt=prompt,
            context={"role": "narrative_ai", "data_type": "market_narrative", "horizon": horizon},
            max_tokens=220,
            temperature=0.4,
        )
        return getattr(response, "response", "") or ""

    def symbol_narrative(
        self,
        symbol: str,
        horizon: str,
        research_summary: Optional[str] = None,
        sentiment_summary: Optional[str] = None,
        market_data: Dict[str, Any] | None = None,
    ) -> str:
        """
        Generate symbol-level narrative that contextualizes research.
        """
        combined_research = research_summary or self.research_ai.summarize_news([symbol])
        prompt = (
            "You are Narrative AI. Provide a concise, non-directive narrative for the symbol below.\n"
            f"Symbol: {symbol}\n"
            f"Horizon: {horizon}\n"
            f"Research summary: {combined_research}\n"
            f"Sentiment summary: {sentiment_summary or 'unknown'}\n"
            f"Market snapshot: {market_data or 'n/a'}\n"
            "Explain tone, catalysts, and risks. Do not suggest trades."
        )
        response = self.llm_runner(
            prompt=prompt,
            context={"role": "narrative_ai", "data_type": "symbol_narrative", "symbol": symbol, "horizon": horizon},
            max_tokens=240,
            temperature=0.4,
        )
        return getattr(response, "response", "") or ""

