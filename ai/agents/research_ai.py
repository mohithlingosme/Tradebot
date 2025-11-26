from __future__ import annotations

"""
Research AI agent.

This agent ONLY gathers and summarizes information (news, sentiment, data).
It never generates trade instructions or orders.
"""

from typing import Any, Callable, Dict, List, Sequence


PromptRunner = Callable[..., Any]


class ResearchAI:
    """Summarizes pre-fetched news and sentiment for downstream consumers."""

    def __init__(self, llm_runner: PromptRunner):
        self.llm_runner = llm_runner

    def summarize_news(self, symbols: List[str], articles: Sequence[Dict[str, Any]] | None = None) -> str:
        """
        Condense news for the given symbols into a short, neutral summary.

        Parameters:
            symbols: list of tickers/indices
            articles: optional pre-fetched articles passed in by the caller
        """
        prompt = (
            "You are Research AI. Summarize recent market news for the symbols below.\n"
            "Keep it factual, bullet-style, and avoid any trade instructions.\n"
            f"Symbols: {', '.join(symbols)}\n"
            f"Articles (may be empty): {articles or 'No articles provided'}\n"
        )
        response = self.llm_runner(
            prompt=prompt,
            context={"role": "research_ai", "data_type": "news_summary"},
            max_tokens=220,
            temperature=0.3,
        )
        return getattr(response, "response", "") or ""

    def summarize_sentiment(self, symbols: List[str], sentiment_samples: Sequence[Dict[str, Any]] | None = None) -> str:
        """
        Summarize sentiment signals (social, options, flows) for symbols.

        This method never recommends trades; it only surfaces tone and risks.
        """
        prompt = (
            "You are Research AI. Summarize current sentiment and positioning for the symbols below.\n"
            "Focus on tone (bullish/bearish/uncertain), drivers, and data quality.\n"
            "Do NOT provide buy/sell instructions or order sizes.\n"
            f"Symbols: {', '.join(symbols)}\n"
            f"Sentiment inputs: {sentiment_samples or 'No sentiment data provided'}\n"
        )
        response = self.llm_runner(
            prompt=prompt,
            context={"role": "research_ai", "data_type": "sentiment_summary"},
            max_tokens=200,
            temperature=0.35,
        )
        return getattr(response, "response", "") or ""

