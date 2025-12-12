"""AI query router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai.agents.narrative_ai import NarrativeAI
from ai.agents.research_ai import ResearchAI
from ai_models.llm import mock_llm_runner
from ai_models.pipeline import AIResponse, FinbotAIPipeline
from ai_models.safety import SafetyLayer

router = APIRouter(prefix="/ai", tags=["ai"])

# In production inject dependencies via container; for now create basic stubs.
safety_layer = SafetyLayer()


class DummyRetriever:
    async def search(self, query: str):
        return ["Finbot currently tracks equities and ETFs.", "Data latency under 150ms for cached endpoints."]


class DummyLLM:
    async def generate(self, prompt: str):
        return "Finbot offers AI insights with strict safety filters and grounded financial data."


pipeline = FinbotAIPipeline(DummyLLM(), DummyRetriever(), safety_layer)


class QueryPayload(BaseModel):
    question: str
    user_id: str | None = "anonymous"


@router.get("/explain_trade/{trade_id}")
async def explain_trade(trade_id: str):
    """
    Generates an explanation for a given trade.
    """
    # TODO: Fetch real trade details from the database using the trade_id
    mock_trade_details = {
        "symbol": "AAPL",
        "entry_price": 150.0,
        "exit_price": 155.0,
        "pnl": 5.0,
        "strategy": "ema_crossover",
    }

    research_ai = ResearchAI(llm_runner=mock_llm_runner)
    narrative_ai = NarrativeAI(research_ai=research_ai, llm_runner=mock_llm_runner)

    explanation = narrative_ai.symbol_narrative(
        symbol=mock_trade_details["symbol"],
        horizon="intraday",
        market_data=mock_trade_details,
    )
    return {"trade_id": trade_id, "explanation": explanation}



@router.get("/explain_strategy/{strategy_name}")
async def explain_strategy(strategy_name: str):
    """
    Generates an explanation for a given strategy.
    """
    research_ai = ResearchAI(llm_runner=mock_llm_runner)
    narrative_ai = NarrativeAI(research_ai=research_ai, llm_runner=mock_llm_runner)

    explanation = narrative_ai.market_narrative(index=strategy_name, horizon="long-term")
    return {"strategy": strategy_name, "explanation": explanation}

