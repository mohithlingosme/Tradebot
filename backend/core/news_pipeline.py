"""
AI-enhanced financial news pipeline.

Responsibilities:
- Scrape articles from configured sources (RSS/JSON feeds)
- Paraphrase content and enrich metadata for SEO
- Persist articles for serving via API and publishing jobs
- Provide daily scheduler for auto-refresh
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import httpx
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from zoneinfo import ZoneInfo

from ..config import get_config
from .ai_pipeline import PromptRequest, ai_pipeline


logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Canonical article representation within the pipeline."""

    title: str
    summary: str
    content: str
    url: str
    source: str
    published_at: datetime
    sentiment: Optional[str] = None
    symbols: List[str] = field(default_factory=list)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    external_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
            "sentiment": self.sentiment,
            "symbols": json.dumps(self.symbols),
            "seo_title": self.seo_title or self.title,
            "seo_description": self.seo_description or self.summary,
            "external_id": self.external_id or self.url,
            "tags": json.dumps(self.tags),
        }


class NewsScraper:
    """Scrapes news content from configured sources."""

    def __init__(self, sources: Optional[List[Dict[str, Any]]] = None):
        self.sources = sources or []

    async def fetch_articles(self, limit: int = 25) -> List[NewsArticle]:
        articles: List[NewsArticle] = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for source in self.sources:
                try:
                    new_articles = await self._fetch_source(client, source)
                    articles.extend(new_articles)
                except Exception as exc:  # pragma: no cover - network variability
                    logger.warning("Failed scraping %s: %s", source.get("name"), exc)
        articles.sort(key=lambda a: a.published_at, reverse=True)
        return articles[:limit]

    async def _fetch_source(self, client: httpx.AsyncClient, source: Dict[str, Any]) -> List[NewsArticle]:
        source_type = source.get("type", "rss")
        url = source["url"]
        response = await client.get(url)
        response.raise_for_status()
        if source_type == "rss":
            return self._parse_rss(response.text, source)
        if source_type == "json":
            return self._parse_json(response.json(), source)
        raise ValueError(f"Unsupported news source type: {source_type}")

    def _parse_rss(self, payload: str, source: Dict[str, Any]) -> List[NewsArticle]:
        from xml.etree import ElementTree as ET

        articles: List[NewsArticle] = []
        root = ET.fromstring(payload)
        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            description = (item.findtext("description") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date_raw = item.findtext("pubDate")
            published_at = self._parse_date(pub_date_raw)

            if not title or not link:
                continue

            article = NewsArticle(
                title=title,
                summary=description,
                content=description,
                url=link,
                source=source.get("name", "rss"),
                published_at=published_at,
                symbols=source.get("symbols", []),
                external_id=item.findtext("guid") or link,
            )
            articles.append(article)
        return articles

    def _parse_json(self, payload: Dict[str, Any], source: Dict[str, Any]) -> List[NewsArticle]:
        articles: List[NewsArticle] = []
        entries = payload.get("articles") or payload.get("data") or []
        for entry in entries:
            title = entry.get("title")
            summary = entry.get("summary") or entry.get("description", "")
            content = entry.get("content") or summary
            url = entry.get("url")
            published_at = self._parse_date(entry.get("published_at") or entry.get("publishedAt"))

            if not title or not url:
                continue

            article = NewsArticle(
                title=title.strip(),
                summary=summary.strip(),
                content=content.strip(),
                url=url.strip(),
                source=source.get("name", "json"),
                published_at=published_at,
                symbols=entry.get("symbols") or source.get("symbols", []),
                sentiment=entry.get("sentiment"),
                external_id=entry.get("id") or url,
            )
            articles.append(article)
        return articles

    def _parse_date(self, value: Optional[str]) -> datetime:
        if not value:
            return datetime.utcnow()
        try:
            return parsedate_to_datetime(value)
        except Exception:
            return datetime.utcnow()


class NewsParaphraser:
    """Uses the AI pipeline to paraphrase and SEO-optimize articles."""

    def __init__(self, enable_ai: bool = True):
        self.enable_ai = enable_ai and ai_pipeline is not None

    def enhance(self, article: NewsArticle) -> NewsArticle:
        if not self.enable_ai:
            article.seo_title = article.title
            article.seo_description = article.summary[:150]
            return article

        prompt = (
            "Paraphrase the following financial news headline and summary for clarity, "
            "add a concise SEO-friendly description, estimate sentiment "
            "(positive/negative/neutral), and list up to 3 tickers mentioned.\n\n"
            f"Title: {article.title}\n"
            f"Summary: {article.summary}\n"
            "Return JSON with fields: title, summary, seo_description, sentiment, symbols."
        )
        try:
            response = ai_pipeline.process_prompt(
                PromptRequest(prompt=prompt, max_tokens=300, temperature=0.4)
            )
            parsed = self._safe_json(response.response)
            article.title = parsed.get("title") or article.title
            article.summary = parsed.get("summary") or article.summary
            article.seo_title = article.title
            article.seo_description = parsed.get("seo_description") or article.summary[:150]
            article.sentiment = parsed.get("sentiment") or article.sentiment
            symbols = parsed.get("symbols") or []
            if isinstance(symbols, str):
                symbols = [symbols]
            article.symbols = [s.upper() for s in symbols] or article.symbols
        except Exception as exc:
            logger.warning("AI paraphrasing failed: %s", exc)
            article.seo_title = article.title
            article.seo_description = article.summary[:150]
        return article

    def _safe_json(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except Exception:
            # Fallback: try to locate JSON substring
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(content[start : end + 1])
                except Exception:
                    return {"summary": content.strip()}
            return {"summary": content.strip()}


class NewsRepository:
    """Handles persistence of news articles."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, future=True)
        self.metadata = MetaData()
        self.table = Table(
            "news_articles",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("title", String(512), nullable=False),
            Column("summary", Text, nullable=False),
            Column("content", Text, nullable=False),
            Column("source", String(128), nullable=False, index=True),
            Column("url", Text, nullable=False, unique=True),
            Column("external_id", String(255), nullable=False, unique=True),
            Column("published_at", DateTime, nullable=False, index=True),
            Column("sentiment", String(32)),
            Column("symbols", Text),
            Column("seo_title", String(512)),
            Column("seo_description", Text),
            Column("tags", Text),
            Column("created_at", DateTime, default=datetime.utcnow),
            Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        )
        self.metadata.create_all(self.engine)

    def save_articles(self, articles: Iterable[NewsArticle]) -> int:
        count = 0
        with self.engine.begin() as conn:
            for article in articles:
                data = article.to_dict()
                stmt = sqlite_insert(self.table).values(
                    **data,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["external_id"],
                    set_={
                        "title": data["title"],
                        "summary": data["summary"],
                        "content": data["content"],
                        "source": data["source"],
                        "url": data["url"],
                        "published_at": data["published_at"],
                        "sentiment": data["sentiment"],
                        "symbols": data["symbols"],
                        "seo_title": data["seo_title"],
                        "seo_description": data["seo_description"],
                        "tags": data["tags"],
                        "updated_at": datetime.utcnow(),
                    },
                )
                conn.execute(stmt)
                count += 1
        return count

    def list_articles(
        self,
        limit: int = 20,
        source: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(self.table).order_by(self.table.c.published_at.desc()).limit(limit)
        if source:
            stmt = stmt.where(self.table.c.source == source)
        rows: List[Dict[str, Any]] = []
        with self.engine.begin() as conn:
            for record in conn.execute(stmt):
                row = dict(record)
                symbols = json.loads(row.get("symbols") or "[]")
                if symbol and symbol.upper() not in symbols:
                    continue
                row["symbols"] = symbols
                row["tags"] = json.loads(row.get("tags") or "[]")
                rows.append(row)
        return rows


class NewsService:
    """High-level API orchestrating scraping, enrichment, and publishing."""

    def __init__(self, config: Dict[str, Any], global_config: Dict[str, Any]):
        database_url = config.get("database_url") or global_config["database"]["url"] or "sqlite:///news.db"
        self.repository = NewsRepository(database_url)
        self.scraper = NewsScraper(config.get("sources"))
        self.paraphraser = NewsParaphraser(enable_ai=config.get("enable_ai", True))
        self.publish_limit = config.get("max_articles", 25)

    async def refresh_news(self) -> int:
        raw_articles = await self.scraper.fetch_articles(limit=self.publish_limit)
        enriched = [self.paraphraser.enhance(article) for article in raw_articles]
        saved = self.repository.save_articles(enriched)
        logger.info("News refresh completed: %s articles saved", saved)
        return saved

    def list_news(self, limit: int = 20, source: Optional[str] = None, symbol: Optional[str] = None):
        return self.repository.list_articles(limit=limit, source=source, symbol=symbol)


class NewsPublishingScheduler:
    """Simple scheduler that triggers the news refresh once per day."""

    def __init__(self, service: NewsService, run_time: str, timezone: str):
        self.service = service
        self.run_time = run_time
        self.timezone = timezone
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    def start(self):
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("News publishing scheduler started")

    async def stop(self):
        if self._task:
            self._stop_event.set()
            await self._task
            logger.info("News publishing scheduler stopped")

    async def trigger_now(self):
        await self.service.refresh_news()

    async def _run_loop(self):
        while not self._stop_event.is_set():
            wait_seconds = self._seconds_until_next_run()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=wait_seconds)
                if self._stop_event.is_set():
                    break
            except asyncio.TimeoutError:
                pass
            await self.service.refresh_news()

    def _seconds_until_next_run(self) -> float:
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)
        hour, minute = (int(part) for part in self.run_time.split(":"))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return max((target - now).total_seconds(), 1.0)


_news_service: Optional[NewsService] = None
_news_scheduler: Optional[NewsPublishingScheduler] = None


def get_news_service() -> NewsService:
    global _news_service
    if _news_service is None:
        config = get_config()
        news_config = config.get("news", {})
        _news_service = NewsService(news_config, config)
    return _news_service


def get_news_scheduler() -> Optional[NewsPublishingScheduler]:
    global _news_scheduler
    service = get_news_service()
    config = get_config()
    scheduler_cfg = config.get("news", {}).get("scheduler", {})
    if not scheduler_cfg.get("enabled", True):
        return None
    if _news_scheduler is None:
        run_time = scheduler_cfg.get("run_time", "06:00")
        timezone = scheduler_cfg.get("timezone", "UTC")
        _news_scheduler = NewsPublishingScheduler(service, run_time, timezone)
    return _news_scheduler

