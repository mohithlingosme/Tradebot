"""
AI endpoints for Finbot
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from ..core import ai_pipeline, PromptRequest, PromptResponse
from .auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])


class MarketAnalysisRequest(BaseModel):
    """Market analysis request."""
    symbol: str
    market_data: Dict


class PortfolioAdviceRequest(BaseModel):
    """Portfolio advice request."""
    portfolio_data: Dict


class ResearchAssistantRequest(BaseModel):
    """Request for research brief."""
    topic: str
    focus_areas: Optional[List[str]] = None


class TradingAssistantRequest(BaseModel):
    """Trading assistant request."""
    symbol: str
    risk_profile: str = Field(default="moderate")
    account_size: float = Field(default=10000, gt=0)


class Holding(BaseModel):
    symbol: str
    weight: float = 0.1
    expected_return: float = 0.08
    volatility: float = 0.2


class PortfolioOptimizerRequest(BaseModel):
    """Advanced portfolio optimizer request."""
    holdings: List[Holding]
    risk_profile: str = "moderate"


class DecisionAssistantRequest(BaseModel):
    """Decision-making AI request."""
    company: str
    question: str


@router.post("/analyze-market", response_model=Dict)
async def analyze_market(
    request: MarketAnalysisRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Analyze market data and provide trading signal.

    Args:
        request: Market analysis request
        current_user: Authenticated user

    Returns:
        Market analysis result
    """
    try:
        payload = ai_pipeline.analyze_market_signal(
            request.symbol,
            request.market_data
        )
        return {
            "symbol": request.symbol,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            **payload,
        }
    except Exception as e:
        logger.error(f"Error analyzing market: {e}")
        raise HTTPException(status_code=500, detail="Market analysis failed")


@router.post("/portfolio-advice", response_model=Dict)
async def get_portfolio_advice(
    request: PortfolioAdviceRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get portfolio optimization advice.

    Args:
        request: Portfolio advice request
        current_user: Authenticated user

    Returns:
        Portfolio advice
    """
    try:
        payload = ai_pipeline.get_portfolio_advice(request.portfolio_data)
        return {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            **payload,
        }
    except Exception as e:
        logger.error(f"Error getting portfolio advice: {e}")
        raise HTTPException(status_code=500, detail="Portfolio analysis failed")


@router.post("/research-assistant", response_model=Dict)
async def research_assistant(
    request: ResearchAssistantRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """Generate AI research brief."""
    try:
        payload = ai_pipeline.generate_research_brief(request.topic, request.focus_areas)
        payload["topic"] = request.topic
        return payload
    except Exception as exc:
        logger.error("Research assistant error: %s", exc)
        raise HTTPException(status_code=500, detail="Research assistant failed")


@router.post("/trading-assistant", response_model=Dict)
async def trading_assistant(
    request: TradingAssistantRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """Provide AI-based trading plan."""
    try:
        payload = ai_pipeline.generate_trading_plan(
            request.symbol, request.risk_profile, request.account_size
        )
        payload["symbol"] = request.symbol
        payload.setdefault("plan", {})
        return payload
    except Exception as exc:
        logger.error("Trading assistant error: %s", exc)
        raise HTTPException(status_code=500, detail="Trading assistant failed")


@router.post("/portfolio-optimizer", response_model=Dict)
async def portfolio_optimizer(
    request: PortfolioOptimizerRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """Optimize allocations with AI commentary."""
    try:
        result = ai_pipeline.optimize_portfolio(
            [holding.dict() for holding in request.holdings],
            request.risk_profile
        )
        return result
    except Exception as exc:
        logger.error("Portfolio optimizer error: %s", exc)
        raise HTTPException(status_code=500, detail="Portfolio optimizer failed")


@router.post("/decision-analyst", response_model=Dict)
async def decision_analyst(
    request: DecisionAssistantRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """Summarize historical decisions for similar contexts."""
    try:
        analysis = ai_pipeline.analyze_company_decision(request.company, request.question)
        return analysis
    except Exception as exc:
        logger.error("Decision analyst error: %s", exc)
        raise HTTPException(status_code=500, detail="Decision analysis failed")


@router.post("/prompt", response_model=PromptResponse)
async def process_prompt(
    request: PromptRequest,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Process a general AI prompt.

    Args:
        request: Prompt request
        current_user: Authenticated user

    Returns:
        AI response
    """
    try:
        response = ai_pipeline.process_prompt(request)
        return response
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        raise HTTPException(status_code=500, detail="Prompt processing failed")

