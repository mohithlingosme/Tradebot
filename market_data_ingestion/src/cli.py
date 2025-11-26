import argparse
import asyncio
import json

from market_data_ingestion.core.backfill import backfill_api, ingest_csv, fetch_csv
from market_data_ingestion.core.dlq import reprocess_dlq
from market_data_ingestion.core.storage import DataStorage
from market_data_ingestion.src.settings import settings
from market_data_ingestion.src.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Market data ingestion utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    backfill_cmd = sub.add_parser("backfill-api")
    backfill_cmd.add_argument("--adapter", required=True)
    backfill_cmd.add_argument("--symbols", required=True, help="Comma separated symbols")
    backfill_cmd.add_argument("--start", required=True)
    backfill_cmd.add_argument("--end", required=True)
    backfill_cmd.add_argument("--interval", default="1m")
    backfill_cmd.add_argument("--config", help="JSON string with adapter config")

    csv_cmd = sub.add_parser("backfill-csv")
    csv_cmd.add_argument("--url", required=True)
    csv_cmd.add_argument("--provider", required=True)

    dlq_cmd = sub.add_parser("replay-dlq")
    dlq_cmd.add_argument("--limit", type=int, default=100)

    args = parser.parse_args()

    storage = DataStorage(settings.database_url)
    await storage.connect()
    await storage.create_tables()

    if args.command == "backfill-api":
        config = json.loads(args.config) if args.config else {}
        res = await backfill_api(
            storage,
            adapter_name=args.adapter,
            adapter_config=config,
            symbols=[s.strip() for s in args.symbols.split(",")],
            start=args.start,
            end=args.end,
            interval=args.interval,
        )
        logger.info(f"Backfill complete: {res}")
    elif args.command == "backfill-csv":
        csv_content = await fetch_csv(args.url)
        res = await ingest_csv(storage, csv_content, provider=args.provider)
        logger.info(f"CSV backfill complete: {res}")
    elif args.command == "replay-dlq":
        count = await reprocess_dlq(storage, limit=args.limit)
        logger.info(f"Replayed {count} DLQ events")

    await storage.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
