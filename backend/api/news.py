"""
API router for AI-enhanced financial news.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .auth import get_current_active_user
from ..core.news_pipeline import get_news_scheduler, get_news_service


router = APIRouter(prefix="/news", tags=["news"])


class NewsItemResponse(BaseModel):
    id: Optional[int]
    title: str
    summary: str
    source: str
    url: str
    published_at: str
    sentiment: Optional[str] = None
    symbols: List[str] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None


@router.get("", response_model=List[NewsItemResponse])
async def list_news(
    limit: int = Query(20, ge=1, le=100),
    source: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None, description="Filter by ticker symbol"),
):
    """Return curated financial news articles."""
    service = get_news_service()
    articles = service.list_news(limit=limit, source=source, symbol=symbol)
    return articles


class RefreshResponse(BaseModel):
    processed: int


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_news(current_user=Depends(get_current_active_user)):
    """Trigger scraping/paraphrasing pipeline manually (protected)."""
    service = get_news_service()
    processed = await service.refresh_news()
    return RefreshResponse(processed=processed)


@router.post("/publish/daily", response_model=RefreshResponse)
async def trigger_daily_publish(current_user=Depends(get_current_active_user)):
    """Run the scheduled publish job immediately."""
    scheduler = get_news_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="News scheduler disabled")
    await scheduler.trigger_now()
    return RefreshResponse(processed=1)

