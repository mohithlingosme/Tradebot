import argparse
import asyncio

from ai.agents.narrative_ai import NarrativeAI
from ai.agents.research_ai import ResearchAI
from ai_models.llm import mock_llm_runner


async def explain_strategy(strategy_name: str):
    """
    Generates an explanation for a given strategy.
    """
    research_ai = ResearchAI(llm_runner=mock_llm_runner)
    narrative_ai = NarrativeAI(research_ai=research_ai, llm_runner=mock_llm_runner)

    explanation = narrative_ai.market_narrative(index=strategy_name, horizon="long-term")

    print("========================================")
    print(f"Explanation for strategy: {strategy_name}")
    print("========================================")
    print(explanation)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Explain a trading strategy.")
    parser.add_argument(
        "--strategy",
        type=str,
        default="ema_crossover",
        help="The name of the strategy to explain.",
    )
    args = parser.parse_args()

    asyncio.run(explain_strategy(args.strategy))
