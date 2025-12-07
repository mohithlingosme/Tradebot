#!/usr/bin/env python3
"""
Central developer entrypoint for running Finbot services locally.

Usage:
    python -m scripts.dev_run backend
    python -m scripts.dev_run ingestion
    python -m scripts.dev_run engine
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path
from typing import Iterable

try:
    from common.env import get_mode as _get_env_mode
except Exception:  # pragma: no cover - fallback when package layout changes
    _get_env_mode = None

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging() -> None:
    """Configure a consistent console logger for the launcher."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=DEFAULT_LOG_FORMAT,
    )


def get_mode() -> str:
    """Return the active mode (dev/paper/live) with a safe default."""
    if _get_env_mode:
        try:
            return _get_env_mode()
        except ValueError:
            return "dev"
    return os.getenv("FINBOT_MODE", "dev").strip().lower()


def read_env_file(env_path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines from a .env-style file."""
    env: dict[str, str] = {}
    try:
        content = env_path.read_text(encoding="utf-8")
    except OSError:
        return env

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def load_mode_env(mode: str | None = None, base_dir: Path | None = None) -> dict[str, str]:
    """Load .env.<mode> into os.environ without overriding explicit env vars."""
    target_mode = (mode or get_mode() or "dev").lower()
    env_dir = base_dir or Path.cwd()
    env_file = env_dir / f".env.{target_mode}"
    values = read_env_file(env_file)
    for key, value in values.items():
        if key not in os.environ:
            os.environ[key] = value
    return values


def _format_symbols(symbols: Iterable[str]) -> str:
    return ", ".join(symbols) if symbols else "<none>"


def start_backend(host: str | None = None, port: int | None = None) -> None:
    """Start the FastAPI backend using uvicorn."""
    try:
        from backend.app import main as backend_main
    except Exception as exc:  # pragma: no cover - import guard for dev ergonomics
        logging.error("Failed to import backend app: %s", exc)
        raise

    import uvicorn

    resolved_host = host or os.getenv("BACKEND_HOST", "127.0.0.1")
    resolved_port = int(port or os.getenv("BACKEND_PORT", "8000"))
    logging.info(
        "Starting backend API (mode=%s) on %s:%s",
        get_mode(),
        resolved_host,
        resolved_port,
    )
    uvicorn.run(
        backend_main.app,
        host=resolved_host,
        port=resolved_port,
        reload=get_mode() == "dev",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


def start_ingestion(host: str | None = None, port: int | None = None) -> None:
    """Start the market data ingestion API via uvicorn."""
    try:
        from market_data_ingestion.src import api as ingestion_api
        from market_data_ingestion.src.settings import settings as ingestion_settings
    except Exception as exc:  # pragma: no cover - import guard for dev ergonomics
        logging.error("Failed to import ingestion service: %s", exc)
        raise

    import uvicorn

    resolved_host = host or os.getenv("MARKET_DATA_HOST", "127.0.0.1")
    resolved_port = int(port or os.getenv("MARKET_DATA_PORT", ingestion_settings.api_port))
    logging.info(
        "Starting ingestion API (mode=%s) on %s:%s",
        get_mode(),
        resolved_host,
        resolved_port,
    )
    uvicorn.run(
        ingestion_api.app,
        host=resolved_host,
        port=resolved_port,
        reload=get_mode() == "dev",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


def _map_trading_mode(finbot_mode: str):
    """Translate FINBOT_MODE into a TradingMode enum instance."""
    from trading_engine import TradingMode

    if finbot_mode == "live":
        return TradingMode.LIVE
    if finbot_mode == "paper":
        return TradingMode.PAPER_TRADING
    return TradingMode.SIMULATION


async def start_engine() -> None:
    """Start the live trading engine in a development-safe loop."""
    try:
        from trading_engine import (
            AdaptiveRSIMACDStrategy,
            LiveTradingConfig,
            LiveTradingEngine,
            StrategyManager,
        )
    except Exception as exc:  # pragma: no cover - import guard for dev ergonomics
        logging.error("Trading engine imports failed: %s", exc)
        raise

    try:
        from backend.risk_management import PortfolioManager
    except Exception:
        from backend.risk_management.portfolio_manager import PortfolioManager  # type: ignore

    finbot_mode = get_mode()
    trading_mode = _map_trading_mode(finbot_mode)

    strategy_manager = StrategyManager()
    if AdaptiveRSIMACDStrategy:
        strategy_manager.load_strategy(
            "adaptive_rsi_macd",
            AdaptiveRSIMACDStrategy,
            {"name": "adaptive_rsi_macd"},
        )
        strategy_manager.activate_strategy("adaptive_rsi_macd")

    portfolio_manager = PortfolioManager(
        {
            "initial_cash": 100000,
            "max_drawdown": 0.15,
            "max_daily_loss": 0.05,
            "max_position_size": 0.10,
        }
    )

    engine = LiveTradingEngine(
        config=LiveTradingConfig(
            mode=trading_mode,
            symbols=["AAPL"],
            update_interval_seconds=float(os.getenv("ENGINE_UPDATE_INTERVAL", "5.0")),
        ),
        strategy_manager=strategy_manager,
        portfolio_manager=portfolio_manager,
    )

    logging.info(
        "Starting trading engine (mode=%s, symbols=%s)",
        finbot_mode,
        _format_symbols(engine.config.symbols),
    )

    started = await engine.start()
    if not started:
        logging.error("Trading engine failed to start; check logs for details")
        return

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping trading engine...")
        await engine.stop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Finbot services locally (backend, ingestion, engine)."
    )
    parser.add_argument(
        "service",
        choices=["backend", "ingestion", "engine"],
        help="Which service to start.",
    )
    parser.add_argument(
        "--host",
        help="Override host (backend/ingestion only). Defaults to env or 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Override port (backend/ingestion only). Defaults to env or service default.",
    )
    args = parser.parse_args()

    configure_logging()
    logging.info("FINBOT_MODE=%s", get_mode())

    if args.service == "backend":
        start_backend(host=args.host, port=args.port)
    elif args.service == "ingestion":
        start_ingestion(host=args.host, port=args.port)
    elif args.service == "engine":
        asyncio.run(start_engine())


if __name__ == "__main__":
    main()
