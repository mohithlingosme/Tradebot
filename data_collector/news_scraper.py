from __future__ import annotations

"""
News & sentiment scraper (Phase 3.2).
"""

import asyncio
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from .config import DataCollectorSettings, get_settings
from .db import PostgresClient
from .models import DailySentiment, NewsArticle
from .utils import stable_hash, to_market_date

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Thin wrapper around VADER with stable labels."""

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def score(self, text: str) -> tuple[float, str]:
        if not text:
            return 0.0, "neutral"
        score = self.analyzer.polarity_scores(text)["compound"]
        if score >= 0.05:
            label = "positive"
        elif score <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        return score, label


class NewsScraper:
    """
    Pulls news articles and maps them to symbols with sentiment attribution.
    """

    def __init__(self, settings: Optional[DataCollectorSettings] = None, db: Optional[PostgresClient] = None):
        self.settings = settings or get_settings()
        self.db = db or PostgresClient(self.settings.database_url)
        self.sentiment = SentimentAnalyzer()

    async def __aenter__(self) -> "NewsScraper":
        await self.db.connect()
        await self.db.ensure_phase3_schema()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.db.close()

    @staticmethod
    def _clean_text(text: str | None) -> str:
        if not text:
            return ""
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text(" ", strip=True)

    def _normalize_article(
        self,
        payload: Dict[str, Any],
        symbol: str,
        company_name: Optional[str] = None,
    ) -> NewsArticle:
        title = payload.get("title") or ""
        description = payload.get("description") or ""
        content = payload.get("content") or ""
        combined_text = " ".join([title, description, content])
        cleaned = self._clean_text(combined_text)
        score, label = self.sentiment.score(cleaned)

        url = payload.get("url") or ""
        article_id = stable_hash(url or combined_text)

        published_at_raw = payload.get("publishedAt") or payload.get("published_at")
        if isinstance(published_at_raw, str):
            published_at = datetime.fromisoformat(published_at_raw.replace("Z", "+00:00"))
        elif isinstance(published_at_raw, datetime):
            published_at = published_at_raw
        else:
            published_at = datetime.utcnow()

        return NewsArticle(
            article_id=article_id,
            symbol=symbol or "MARKET",
            company_name=company_name,
            headline=title.strip(),
            summary=description.strip() or None,
            source=(payload.get("source") or {}).get("name")
            if isinstance(payload.get("source"), dict)
            else payload.get("source"),
            url=url,
            published_at=published_at,
            sentiment_score=score,
            sentiment_label=label,
            raw=payload,
        )

    @staticmethod
    def _build_symbol_map(symbols: Sequence[str], company_names: Optional[Dict[str, str]] = None) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {}
        for symbol in symbols:
            mapping[symbol] = [symbol]
            if company_names and company_names.get(symbol):
                mapping[symbol].append(company_names[symbol])
        return mapping

    def _map_article_to_symbols(
        self, payload: Dict[str, Any], symbol_map: Dict[str, List[str]]
    ) -> List[str]:
        haystack = " ".join(
            [
                str(payload.get("title", "")),
                str(payload.get("description", "")),
                str(payload.get("content", "")),
            ]
        ).lower()

        matched: List[str] = []
        for symbol, aliases in symbol_map.items():
            for alias in aliases:
                if alias and alias.lower() in haystack:
                    matched.append(symbol)
                    break
        if not matched:
            matched.append("MARKET")
        return matched

    async def _fetch_newsapi_page(
        self, query: str, from_date: date, to_date: date, page: int = 1
    ) -> List[Dict[str, Any]]:
        if not self.settings.news_api_key:
            raise RuntimeError("NEWS_API_KEY not configured")

        params = {
            "q": query,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": self.settings.news_page_size,
            "page": page,
            "apiKey": self.settings.news_api_key,
        }
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            resp = await client.get(self.settings.news_api_endpoint, params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get("articles", [])

    async def fetch_articles(
        self,
        symbols: Sequence[str],
        company_names: Optional[Dict[str, str]] = None,
        days: int = 3,
    ) -> List[NewsArticle]:
        """
        Fetch articles for symbols, company names, and general market terms.
        """
        to_date = date.today()
        from_date = to_date - timedelta(days=days)
        symbol_map = self._build_symbol_map(symbols, company_names)

        queries = list(symbols) + list(self.settings.news_market_terms)
        tasks = [self._fetch_newsapi_page(query, from_date, to_date) for query in queries]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        articles: List[NewsArticle] = []
        for query, payload in zip(queries, responses):
            if isinstance(payload, Exception):
                logger.warning("Failed to fetch articles for query %s: %s", query, payload)
                continue

            for raw_article in payload:
                matched_symbols = self._map_article_to_symbols(raw_article, symbol_map)
                for symbol in matched_symbols:
                    articles.append(self._normalize_article(raw_article, symbol))
        return articles

    @staticmethod
    def aggregate_sentiment(articles: Sequence[NewsArticle]) -> List[DailySentiment]:
        if not articles:
            return []

        grouped: Dict[tuple[str, date], List[float]] = defaultdict(list)
        counts: Dict[tuple[str, date], int] = defaultdict(int)
        max_scores: Dict[tuple[str, date], float] = defaultdict(lambda: float("-inf"))

        for article in articles:
            market_date = to_market_date(article.published_at)
            key = (article.symbol, market_date)
            if article.sentiment_score is not None:
                grouped[key].append(article.sentiment_score)
                max_scores[key] = max(max_scores[key], article.sentiment_score)
            counts[key] += 1

        sentiments: List[DailySentiment] = []
        for (symbol, market_date), scores in grouped.items():
            sentiments.append(
                DailySentiment(
                    symbol=symbol,
                    market_date=market_date,
                    mean_sentiment=float(pd.Series(scores).mean()) if scores else None,
                    max_sentiment=max_scores[(symbol, market_date)]
                    if max_scores[(symbol, market_date)] != float("-inf")
                    else None,
                    article_count=counts[(symbol, market_date)],
                    source="newsapi",
                )
            )
        return sentiments

    async def persist_articles(self, articles: Sequence[NewsArticle]) -> None:
        if not articles:
            return

        query = """
        INSERT INTO news_articles (
            article_id, symbol, company_name, headline, summary, source, url,
            published_at, sentiment_score, sentiment_label, raw, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW()
        )
        ON CONFLICT (article_id, symbol)
        DO UPDATE SET
            headline = EXCLUDED.headline,
            summary = EXCLUDED.summary,
            sentiment_score = EXCLUDED.sentiment_score,
            sentiment_label = EXCLUDED.sentiment_label,
            raw = EXCLUDED.raw
        """
        params = [
            (
                article.article_id,
                article.symbol,
                article.company_name,
                article.headline,
                article.summary,
                article.source,
                article.url,
                article.published_at,
                article.sentiment_score,
                article.sentiment_label,
                article.raw,
            )
            for article in articles
        ]
        await self.db.executemany(query, params)
        logger.info("Persisted %s news articles", len(articles))

    async def persist_daily_sentiment(self, aggregates: Sequence[DailySentiment]) -> None:
        if not aggregates:
            return

        query = """
        INSERT INTO daily_sentiment (
            symbol, market_date, mean_sentiment, max_sentiment, article_count, source, created_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, NOW()
        )
        ON CONFLICT (symbol, market_date, source)
        DO UPDATE SET
            mean_sentiment = EXCLUDED.mean_sentiment,
            max_sentiment = EXCLUDED.max_sentiment,
            article_count = EXCLUDED.article_count
        """
        params = [
            (
                agg.symbol,
                agg.market_date,
                agg.mean_sentiment,
                agg.max_sentiment,
                agg.article_count,
                agg.source,
            )
            for agg in aggregates
        ]
        await self.db.executemany(query, params)
        logger.info("Persisted %s daily sentiment rows", len(aggregates))

    async def run(self, symbols: Sequence[str], company_names: Optional[Dict[str, str]] = None, days: int = 3) -> None:
        articles = await self.fetch_articles(symbols, company_names=company_names, days=days)
        await self.persist_articles(articles)
        aggregates = self.aggregate_sentiment(articles)
        await self.persist_daily_sentiment(aggregates)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    async with NewsScraper(settings=settings) as scraper:
        await scraper.run(symbols=settings.default_symbols, days=3)


if __name__ == "__main__":
    asyncio.run(main())
