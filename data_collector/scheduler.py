from __future__ import annotations

"""
APScheduler-based orchestration for Phase 3 jobs (Phase 3.6).
"""

import asyncio
import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import get_settings
from .feature_builder import FeatureBuilder
from .fundamentals_scraper import FundamentalsScraper
from .macro_scraper import MacroScraper
from .news_scraper import NewsScraper
from .stock_scraper import StockScraper

logger = logging.getLogger(__name__)
settings = get_settings()


async def run_stock_job() -> None:
    async with StockScraper(settings=settings) as scraper:
        prices, anomalies = await scraper.fetch_and_store_latest(days=30)
        logger.info("Stock job complete. prices=%s anomalies=%s", prices, anomalies)


async def run_news_job() -> None:
    async with NewsScraper(settings=settings) as scraper:
        await scraper.run(symbols=settings.default_symbols, days=2)
        logger.info("News job complete.")


async def run_macro_job() -> None:
    async with MacroScraper(settings=settings) as scraper:
        indicators = await scraper.run()
        logger.info("Macro job complete. count=%s", len(indicators))


async def run_fundamentals_job() -> None:
    async with FundamentalsScraper(settings=settings) as scraper:
        await scraper.refresh_all(settings.default_symbols)
        logger.info("Fundamentals job complete.")


async def run_features_job(days: int = 90) -> None:
    end = date.today()
    start = end - timedelta(days=days)
    async with FeatureBuilder(settings=settings) as builder:
        await builder.build(
            symbols=settings.default_symbols,
            start=start,
            end=end,
            persist_to_db=True,
            write_parquet=True,
        )
        logger.info("Features job complete.")


def _add_jobs(scheduler: AsyncIOScheduler) -> None:
    hour, minute = settings.scheduler_daily_time.split(":")
    base_hour = int(hour)
    base_minute = int(minute)
    news_hour = (base_hour + (base_minute + 15) // 60) % 24
    news_minute = (base_minute + 15) % 60
    features_hour = (base_hour + (base_minute + 45) // 60) % 24
    features_minute = (base_minute + 45) % 60
    scheduler.add_job(
        lambda: asyncio.create_task(run_stock_job()),
        trigger=CronTrigger(hour=base_hour, minute=base_minute, timezone=settings.scheduler_timezone),
        id="stock_daily",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(run_news_job()),
        trigger=CronTrigger(hour=news_hour, minute=news_minute, timezone=settings.scheduler_timezone),
        id="news_daily",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(run_features_job()),
        trigger=CronTrigger(hour=features_hour, minute=features_minute, timezone=settings.scheduler_timezone),
        id="features_daily",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(run_macro_job()),
        trigger=CronTrigger(day_of_week=settings.scheduler_weekly_day, hour=5, minute=30, timezone=settings.scheduler_timezone),
        id="macro_weekly",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(run_fundamentals_job()),
        trigger=CronTrigger(day_of_week=settings.scheduler_weekly_day, hour=6, minute=0, timezone=settings.scheduler_timezone),
        id="fundamentals_weekly",
        max_instances=1,
        replace_existing=True,
    )


async def start_scheduler() -> None:
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled via configuration")
        return

    logging.getLogger("apscheduler").setLevel(logging.INFO)
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    _add_jobs(scheduler)
    scheduler.start()
    logger.info("Scheduler started with timezone %s", settings.scheduler_timezone)

    # Keep the loop alive
    stop_event = asyncio.Event()
    await stop_event.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_scheduler())
