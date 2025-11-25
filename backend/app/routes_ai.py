"""AI query router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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


@router.post("/query", response_model=AIResponse)
async def query_ai(payload: QueryPayload):
    question = payload.question
    user_id = payload.user_id or "anonymous"
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")
    return await pipeline.answer(user_id=user_id, question=question)
