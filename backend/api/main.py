"""
FastAPI Backend API

Responsibilities:
- Expose REST/WebSocket endpoints for dashboard
- Handle authentication and authorization
- Provide configuration and status endpoints

Endpoints:
- GET /status - Service status
- GET /health - Detailed health check
- GET /metrics - Performance metrics
- GET /portfolio - Portfolio summary
- GET /positions - Current positions
- POST /auth/login - User authentication
- POST /auth/logout - User logout
- POST /trades - Place trade orders
- POST /strategies/{action} - Strategy management
- WebSocket /ws/trades - Real-time trade updates
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

from .auth import (
    UserCredentials,
    TokenResponse,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
)
from ..config import settings
try:
    from ..trading_engine import (
        StrategyManager, AdaptiveRSIMACDStrategy,
        LiveTradingEngine, LiveTradingConfig, TradingMode
    )
    from ..risk_management import PortfolioManager
    from ..monitoring import get_logger
except ImportError:
    # Mock imports for testing
    StrategyManager = None
    AdaptiveRSIMACDStrategy = None
    LiveTradingEngine = None
    LiveTradingConfig = None
    TradingMode = None
    PortfolioManager = None
    get_logger = lambda: None

try:
    from .mvp import mvp_engine
except Exception:
    mvp_engine = None

# Global configuration
APP_START_TIME = datetime.utcnow()
EXTERNAL_HEALTH_ENDPOINTS = {
    "alphavantage": os.getenv("ALPHAVANTAGE_HEALTH_URL", "https://www.alphavantage.co"),
    "yahoo_finance": os.getenv(
        "YAHOO_FINANCE_HEALTH_URL",
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=AAPL"
    ),
}

# Import market data router
try:
    from .market_data import router as market_data_router
    MARKET_DATA_AVAILABLE = True
except ImportError:
    MARKET_DATA_AVAILABLE = False
    logger.warning("Market data router not available")

# Import news router / scheduler
try:
    from .news import router as news_router
    from ..core.news_pipeline import get_news_scheduler
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    news_router = None
    logger.warning("News router not available")


def _determine_engine_mode() -> Optional["TradingMode"]:
    """
    Map FINBOT_MODE into a trading engine mode while enforcing the live
    confirmation guard.
    """
    if not TradingMode:
        return None

    if settings.finbot_mode == "live":
        if not settings.live_trading_confirm:
            logger.warning(
                "FINBOT_MODE=live without FINBOT_LIVE_TRADING_CONFIRM; "
                "downgrading to paper trading mode"
            )
            return TradingMode.PAPER_TRADING
        return TradingMode.LIVE

    if settings.finbot_mode == "paper":
        return TradingMode.PAPER_TRADING

    return TradingMode.SIMULATION


def ensure_live_trading_allowed(operation: str) -> None:
    """
    Guard any live broker calls behind explicit mode + confirmation flags.
    """
    if settings.finbot_mode != "live":
        raise HTTPException(
            status_code=403,
            detail=f"Live trading is disabled while FINBOT_MODE={settings.finbot_mode}. "
            "Switch to FINBOT_MODE=live to enable broker operations.",
        )

    if not settings.live_trading_confirm:
        raise HTTPException(
            status_code=403,
            detail=(
                f"{operation} blocked: set FINBOT_LIVE_TRADING_CONFIRM=true to unlock "
                "live broker calls."
            ),
        )

app = FastAPI(
    title="Finbot Trading API",
    description="API for Finbot autonomous trading system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Import core services
cache_manager = None
try:
    from ..core import RateLimitMiddleware, cache_manager
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60, requests_per_hour=1000)
    logger.info("Rate limiting middleware enabled")
except ImportError:
    logger.warning("Rate limiting middleware not available")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:5173", "http://localhost:3000"],  # Streamlit, Vite, React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lightweight latency observer to keep responses fast.
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000
    response.headers["X-Process-Time-ms"] = f"{process_time_ms:.2f}"
    if process_time_ms > 150:
        logger.warning(f"Slow response {request.url.path}: {process_time_ms:.2f}ms")
    return response

# Global service instances (in production, use dependency injection)
strategy_manager = StrategyManager() if StrategyManager else None
portfolio_manager = PortfolioManager({
    'initial_cash': 100000,
    'max_drawdown': 0.15,
    'max_daily_loss': 0.05,
    'max_position_size': 0.10
}) if PortfolioManager else None
logger_service = get_logger()

# Live trading engine
engine_mode = _determine_engine_mode() if LiveTradingConfig else None
live_engine_config = LiveTradingConfig(
    mode=engine_mode or (TradingMode.SIMULATION if TradingMode else None),
    symbols=["AAPL"],
    update_interval_seconds=5.0
) if LiveTradingConfig else None
live_trading_engine = LiveTradingEngine(
    config=live_engine_config,
    strategy_manager=strategy_manager,
    portfolio_manager=portfolio_manager
) if LiveTradingEngine else None

class LogEntry(BaseModel):
    """Structured log entry returned by the /logs endpoint."""

    timestamp: datetime
    level: str
    message: str
    logger: Optional[str] = None
    trace_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_SECRET_KEYS = ("token", "secret", "password", "api_key", "apikey", "authorization", "bearer")
_SECRET_PATTERN = re.compile(r"(?i)(token|secret|password|api[_-]?key|authorization|bearer)[:=\s]+([^\s]+)")


def _mask_sensitive(value: Any) -> Any:
    """Mask obvious secrets in strings or dicts to avoid leaking credentials through the API."""
    if isinstance(value, str):
        return _SECRET_PATTERN.sub(lambda m: f"{m.group(1)}=***", value)
    if isinstance(value, dict):
        return {
            key: ("***" if any(k in key.lower() for k in _SECRET_KEYS) else _mask_sensitive(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_mask_sensitive(item) for item in value]
    return value


class TradeStreamManager:
    """In-memory pub/sub manager for trade streaming."""

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue):
        async with self._lock:
            self._subscribers.discard(queue)

    async def broadcast(self, message: Dict[str, Any]):
        async with self._lock:
            subscribers = list(self._subscribers)

        for queue in subscribers:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                # Drop oldest message to keep stream moving
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait(message)

    async def count_subscribers(self) -> int:
        async with self._lock:
            return len(self._subscribers)


trade_stream_manager = TradeStreamManager()


def _resolve_database_url() -> Optional[str]:
    if settings.database_url:
        return settings.database_url

    if (
        settings.database_user
        and settings.database_password
        and settings.database_host
        and settings.database_port
        and settings.database_name
    ):
        return (
            f"postgresql://{settings.database_user}:"
            f"{settings.database_password}@{settings.database_host}:"
            f"{settings.database_port}/{settings.database_name}"
        )

    if settings.database_name:
        return f"sqlite:///{settings.database_name}.db"

    return None


def _check_database_health() -> Dict[str, Any]:
    db_url = _resolve_database_url()
    if not db_url:
        return {"status": "unknown", "details": "Database configuration missing"}

    start = time.perf_counter()
    try:
        engine = create_engine(db_url, future=True)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency = round((time.perf_counter() - start) * 1000, 2)
        engine.dispose()
        return {"status": "healthy", "latency_ms": latency}
    except ModuleNotFoundError as exc:
        logger.error(f"Database driver not installed: {exc}")
        return {"status": "unknown", "details": f"Driver missing: {exc.name}"}
    except SQLAlchemyError as exc:
        logger.error(f"Database health check failed: {exc}")
        return {"status": "unhealthy", "details": str(exc)}


def _hit_endpoint(url: str, timeout: float) -> float:
    request = Request(url, method="HEAD")
    start = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
    except HTTPError as exc:
        status = exc.code
        if status == 405:  # Method not allowed, retry with GET
            request = Request(url, method="GET")
            with urlopen(request, timeout=timeout) as response:
                status = response.status
    except URLError as exc:
        raise RuntimeError(str(exc)) from exc

    if status >= 500:
        raise RuntimeError(f"HTTP {status}")

    latency = round((time.perf_counter() - start) * 1000, 2)
    return latency


def _check_external_services(timeout: float = 3.0) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    for name, url in EXTERNAL_HEALTH_ENDPOINTS.items():
        if not url:
            results[name] = {"status": "unknown", "details": "URL not configured"}
            continue
        try:
            latency = _hit_endpoint(url, timeout)
            results[name] = {"status": "healthy", "latency_ms": latency}
        except Exception as exc:  # pragma: no cover - network edge cases
            results[name] = {"status": "unhealthy", "details": str(exc)}
    return results

# Include market data router if available
if MARKET_DATA_AVAILABLE:
    app.include_router(market_data_router)

if NEWS_AVAILABLE and news_router is not None:
    app.include_router(news_router)

    async def start_news_scheduler():
        scheduler = get_news_scheduler()
        if scheduler:
            scheduler.start()

    async def stop_news_scheduler():
        scheduler = get_news_scheduler()
        if scheduler:
            await scheduler.stop()

    app.add_event_handler("startup", start_news_scheduler)
    app.add_event_handler("shutdown", stop_news_scheduler)

# Include AI router
try:
    from .ai import router as ai_router
    app.include_router(ai_router)
    logger.info("AI router enabled")
except ImportError:
    logger.warning("AI router not available")

# Include paper trading router
try:
    from .paper_trading import router as paper_trading_router
    app.include_router(paper_trading_router)
    logger.info("Paper trading router enabled")
except ImportError:
    logger.warning("Paper trading router not available")

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Finbot Trading API", "version": "1.0.0"}

@app.get("/status")
async def get_status():
    """
    Get service status and health information.

    Returns:
        Dictionary with status information
    """
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "strategy_manager": "active" if strategy_manager else "inactive",
            "portfolio_manager": "active" if portfolio_manager else "inactive",
            "logger": "active" if logger_service else "inactive",
            "market_data": "active" if MARKET_DATA_AVAILABLE else "inactive"
        }
    }

@app.get("/portfolio")
async def get_portfolio():
    """
    Get portfolio summary.

    Returns:
        Portfolio summary dictionary
    """
    if portfolio_manager:
        try:
            return portfolio_manager.get_portfolio_summary()
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    if mvp_engine:
        return mvp_engine.broker.portfolio_summary()
    raise HTTPException(status_code=503, detail="Portfolio manager not available")

@app.get("/positions")
async def get_positions():
    """
    Get current positions.

    Returns:
        List of position dictionaries
    """
    if portfolio_manager:
        try:
            return portfolio_manager.get_position_summary()
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    if mvp_engine:
        return mvp_engine.broker.get_positions()
    raise HTTPException(status_code=503, detail="Portfolio manager not available")

@app.get("/strategies")
async def get_strategies():
    """
    Get available and active strategies.

    Returns:
        Dictionary with strategy information
    """
    if not strategy_manager:
        raise HTTPException(status_code=503, detail="Strategy manager not available")

    try:
        return {
            "available": strategy_manager.get_available_strategies(),
            "active": strategy_manager.get_active_strategies()
        }
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/orders/recent")
async def get_recent_orders(limit: int = 50):
    """Return recent orders (MVP mock broker when available)."""
    if mvp_engine:
        return mvp_engine.broker.get_orders(limit=limit)
    raise HTTPException(status_code=503, detail="Orders not available")

@app.post("/strategies/{action}")
async def manage_strategy(action: str, strategy_name: str):
    """
    Manage strategies (activate/deactivate).

    Args:
        action: 'activate' or 'deactivate'
        strategy_name: Name of strategy

    Returns:
        Operation result
    """
    if not strategy_manager:
        raise HTTPException(status_code=503, detail="Strategy manager not available")

    try:
        if action == "activate":
            success = strategy_manager.activate_strategy(strategy_name)
        elif action == "deactivate":
            success = strategy_manager.deactivate_strategy(strategy_name)
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        if not success:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_name} not found")

        return {"message": f"Strategy {strategy_name} {action}d successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error managing strategy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/strategies/load")
async def load_strategy(strategy_config: Dict):
    """
    Load a new strategy instance.

    Args:
        strategy_config: Strategy configuration including name, class, and params

    Returns:
        Load result
    """
    try:
        strategy_name = strategy_config.get('name')
        strategy_class_name = strategy_config.get('class', 'AdaptiveRSIMACDStrategy')
        config = strategy_config.get('config', {})

        # Map strategy class names to actual classes
        strategy_classes = {
            'AdaptiveRSIMACDStrategy': AdaptiveRSIMACDStrategy
        }

        if strategy_class_name not in strategy_classes:
            raise HTTPException(status_code=400, detail=f"Unknown strategy class: {strategy_class_name}")

        strategy_class = strategy_classes[strategy_class_name]
        success = strategy_manager.load_strategy(strategy_name, strategy_class, config)

        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to load strategy: {strategy_name}")

        return {"message": f"Strategy {strategy_name} loaded successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading strategy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/trading/{action}")
async def control_trading(action: str):
    """
    Control live trading engine (start/stop).

    Args:
        action: 'start' or 'stop'

    Returns:
        Operation result
    """
    try:
        if action == "start":
            import asyncio
            success = await live_trading_engine.start()
        elif action == "stop":
            import asyncio
            success = await live_trading_engine.stop()
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to {action} trading engine")

        return {"message": f"Trading engine {action}ed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling trading: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/trading/status")
async def get_trading_status():
    """
    Get live trading engine status.

    Returns:
        Engine status information
    """
    try:
        return live_trading_engine.get_engine_status()
    except Exception as e:
        logger.error(f"Error getting trading status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/trading/history")
async def get_trading_history(limit: int = 50):
    """
    Get recent trading execution history.

    Args:
        limit: Maximum number of records to return

    Returns:
        List of execution results
    """
    try:
        return live_trading_engine.get_execution_history(limit)
    except Exception as e:
        logger.error(f"Error getting trading history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/logs")
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"),
    limit: int = Query(100, ge=1, le=500, description="Number of log entries to return (max 500)"),
    since: Optional[datetime] = Query(None, description="Return entries after this timestamp"),
    until: Optional[datetime] = Query(None, description="Return entries before this timestamp"),
    current_admin: Dict = Depends(get_current_admin_user),
):
    """
    Return structured log entries with filtering and masking of sensitive data.
    """
    try:
        log_file_path = getattr(settings, 'log_file', None)
        if not log_file_path:
            if mvp_engine:
                return {"logs": mvp_engine.logs, "total_lines": len(mvp_engine.logs), "source": "mvp", "message": "No log file found"}
            return {"logs": [], "total_lines": 0, "message": "Log file configuration missing"}

        log_file = Path(log_file_path)
        if not log_file.exists():
            if mvp_engine:
                return {"logs": mvp_engine.logs, "total_lines": len(mvp_engine.logs), "source": "mvp", "message": "No log file found"}
            return {"logs": [], "total_lines": 0, "message": "No log file found"}

        requested_level = level.upper() if level else None
        if requested_level and requested_level not in _LOG_LEVELS:
            raise HTTPException(status_code=422, detail="Invalid log level filter")

        # Normalize datetime filters to naive UTC for comparison
        if since and since.tzinfo:
            since = since.replace(tzinfo=None)
        if until and until.tzinfo:
            until = until.replace(tzinfo=None)

        try:
            all_lines = log_file.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            logger.error(f"Unable to read log file {log_file}: {exc}")
            # Log store (file) is present but unreadable; surface as service unavailable
            raise HTTPException(status_code=503, detail="Log store unavailable")

        log_entries: List[LogEntry] = []
        line_pattern = re.compile(
            r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (?P<logger>[^-]+) - (?P<level>[^-]+) - (?P<message>.+)$"
        )
        for raw_line in reversed(all_lines):  # Start from newest
            if not raw_line.strip():
                continue

            parsed_entry: Optional[LogEntry] = None

            # Attempt JSON log parsing first
            try:
                as_json = json.loads(raw_line)
                if isinstance(as_json, dict) and {"timestamp", "level", "message"} <= set(as_json.keys()):
                    timestamp = datetime.fromisoformat(as_json["timestamp"])
                    parsed_entry = LogEntry(
                        timestamp=timestamp,
                        level=str(as_json.get("level", "")).upper(),
                        message=_mask_sensitive(as_json.get("message", "")),
                        logger=str(as_json.get("logger", "")) or None,
                        trace_id=as_json.get("trace_id"),
                        extra=_mask_sensitive({k: v for k, v in as_json.items() if k not in {"timestamp", "level", "message", "logger", "trace_id"}}),
                    )
            except (json.JSONDecodeError, ValueError):
                parsed_entry = None

            if not parsed_entry:
                match = line_pattern.match(raw_line.strip())
                if not match:
                    continue

                timestamp_str = match.group("timestamp")
                logger_name = match.group("logger").strip()
                level_name = match.group("level").strip().upper()
                message = match.group("message").strip()

                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                except ValueError:
                    continue

                component_match = re.match(r"^\[(?P<component>[^\]]+)\]\s*(?P<body>.*)$", message)
                component = component_match.group("component") if component_match else None
                body = component_match.group("body") if component_match else message

                data: Dict[str, Any] = {}
                trace_id = None
                duration_ms = None

                parts = [part.strip() for part in body.split("|")]
                message_body = parts[0]

                for part in parts[1:]:
                    if part.lower().startswith("data:"):
                        raw_data = part.split(":", 1)[1].strip()
                        try:
                            data = json.loads(raw_data)
                        except json.JSONDecodeError:
                            data = {"raw": raw_data}
                    elif part.lower().startswith("trace:"):
                        trace_id = part.split(":", 1)[1].strip()
                    elif part.lower().startswith("duration:"):
                        duration_raw = part.split(":", 1)[1].strip().lower().replace("ms", "")
                        try:
                            duration_ms = float(duration_raw)
                        except ValueError:
                            duration_ms = None

                extra: Dict[str, Any] = {"component": component or logger_name}
                if data:
                    extra["data"] = _mask_sensitive(data)
                if duration_ms is not None:
                    extra["duration_ms"] = duration_ms

                parsed_entry = LogEntry(
                    timestamp=timestamp,
                    level=level_name,
                    message=_mask_sensitive(message_body),
                    logger=logger_name,
                    trace_id=trace_id,
                    extra=_mask_sensitive(extra),
                )

            if requested_level and parsed_entry.level.upper() != requested_level:
                continue
            if since and parsed_entry.timestamp < since:
                continue
            if until and parsed_entry.timestamp > until:
                continue

            log_entries.append(parsed_entry)
            if len(log_entries) >= limit:
                break

        return {
            "logs": [entry.dict() for entry in log_entries],
            "total_lines": len(all_lines),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):
    """
    WebSocket endpoint for real-time trade updates.

    Clients can subscribe to live trade updates.
    """
    await websocket.accept()
    subscriber = await trade_stream_manager.subscribe()
    await websocket.send_json(
        {
            "type": "status",
            "timestamp": datetime.now().isoformat(),
            "message": "Subscribed to trade stream",
        }
    )

    try:
        while True:
            try:
                message = await asyncio.wait_for(subscriber.get(), timeout=15)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                await websocket.send_json(
                    {
                        "type": "keepalive",
                        "timestamp": datetime.now().isoformat(),
                        "message": "still connected",
                    }
                )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await trade_stream_manager.unsubscribe(subscriber)
        await websocket.close()


@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """Stream MVP dashboard snapshots (paper mode simulator)."""
    if not mvp_engine:
        await websocket.close(code=1011)
        return
    await websocket.accept()
    subscriber = await mvp_engine.subscribe()
    try:
        await websocket.send_json({"type": "status", "message": "subscribed", "mode": "PAPER"})
        while True:
            try:
                message = await asyncio.wait_for(subscriber.get(), timeout=15)
                await websocket.send_json(message)
            except asyncio.TimeoutError:
                await websocket.send_json(
                    {"type": "keepalive", "timestamp": datetime.now().isoformat(), "mode": "PAPER"}
                )
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket client disconnected")
    finally:
        await mvp_engine.unsubscribe(subscriber)
        await websocket.close()

# Authentication endpoints
@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserCredentials):
    """
    Authenticate user and return JWT token.

    Args:
        credentials: User login credentials

    Returns:
        JWT access token
    """
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username, "role": getattr(user, "role", "user")})
    return TokenResponse(access_token=access_token, expires_in=1800)

@app.post("/auth/logout")
async def logout(current_user: Dict = Depends(get_current_active_user)):
    """
    Logout user (invalidate token on client side).

    Returns:
        Logout confirmation
    """
    # In a stateless JWT system, logout is handled client-side by discarding the token
    # For server-side token invalidation, implement token blacklisting
    return {"message": "Logged out successfully"}

class RegisterRequest(BaseModel):
    """User registration request model."""
    username: str
    email: str
    password: str

@app.post("/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """
    Register a new user.

    Args:
        request: Registration details

    Returns:
        JWT access token
    """
    from .auth import USER_DATABASE, pwd_context
    
    # Check if user already exists
    if request.username in USER_DATABASE:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, request.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Validate password strength
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    # Create new user
    hashed_password = pwd_context.hash(request.password)
    USER_DATABASE[request.username] = {
        "username": request.username,
        "email": request.email,
        "hashed_password": hashed_password,
        "role": "user",
    }
    
    # Create token
    access_token = create_access_token(data={"sub": request.username, "role": "user"})
    logger.info(f"New user registered: {request.username}")
    
    return TokenResponse(access_token=access_token, expires_in=1800)

class ForgotPasswordRequest(BaseModel):
    """Forgot password request model."""
    email: str

@app.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset.

    Args:
        request: Email address

    Returns:
        Confirmation message
    """
    from .auth import USER_DATABASE
    
    # Find user by email
    user = None
    for username, user_data in USER_DATABASE.items():
        if user_data.get("email") == request.email:
            user = username
            break
    
    # Always return success message (security best practice - don't reveal if email exists)
    # In production, send actual password reset email
    logger.info(f"Password reset requested for email: {request.email}")
    
    return {
        "message": "If an account exists with this email, you will receive password reset instructions."
    }


@app.on_event("startup")
async def start_mvp_loop():
    if mvp_engine and settings.finbot_mode != "live":
        await mvp_engine.start()


@app.on_event("shutdown")
async def stop_mvp_loop():
    if mvp_engine and mvp_engine.running:
        await mvp_engine.stop()

# Trade execution model
class TradeRequest(BaseModel):
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: Optional[float] = None  # Market order if None

@app.post("/trades")
async def place_trade(trade: TradeRequest, current_user: Dict = Depends(get_current_active_user)):
    """
    Place a trade order.

    Args:
        trade: Trade order details
        current_user: Authenticated user

    Returns:
        Trade execution result
    """
    try:
        # Validate trade parameters
        if trade.side not in ['buy', 'sell']:
            raise HTTPException(status_code=400, detail="Invalid trade side")

        if trade.quantity <= 0:
            raise HTTPException(status_code=400, detail="Invalid quantity")

        execution_mode = settings.finbot_mode
        live_execution = False

        if settings.finbot_mode == "live":
            ensure_live_trading_allowed("Placing live trade orders")
            live_execution = True
        else:
            logger.warning(
                "Live broker calls are disabled in FINBOT_MODE=%s; using simulated execution",
                settings.finbot_mode,
            )

        # TODO: Implement actual trade execution through broker integration
        # For now, simulate trade execution
        trade_result = {
            "id": f"trade_{datetime.now().timestamp()}",
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.price or 100.0,  # Mock price
            "timestamp": datetime.now().isoformat(),
            "status": "executed",
            "execution_mode": execution_mode,
            "live_execution": live_execution,
        }

        logger.info(f"Trade executed: {trade_result}")
        await trade_stream_manager.broadcast(
            {
                "type": "trade",
                "timestamp": trade_result["timestamp"],
                "trade": trade_result
            }
        )
        return trade_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing trade: {e}")
        raise HTTPException(status_code=500, detail="Trade execution failed")

@app.get("/health")
async def get_health():
    """
    Detailed health check endpoint.

    Returns:
        Comprehensive health status
    """
    services = {
        "strategy_manager": "healthy" if strategy_manager else "unhealthy",
        "portfolio_manager": "healthy" if portfolio_manager else "unhealthy",
        "logger": "healthy" if logger_service else "unhealthy",
        "trading_engine": "healthy" if live_trading_engine else "unhealthy"
    }

    db_health = _check_database_health()
    external_health = _check_external_services()

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": services,
        "database": db_health,
        "external_apis": external_health
    }

    dependency_states = [db_health.get("status")] + [svc.get("status") for svc in external_health.values()]
    if any(state == "unhealthy" for state in dependency_states if state) or \
            any(status == "unhealthy" for status in services.values()):
        health_status["status"] = "degraded"

    return health_status

@app.get("/metrics")
async def get_metrics():
    """
    Get system performance metrics.

    Returns:
        Performance metrics dictionary
    """
    telemetry = logger_service.get_metrics_summary() if logger_service else {}
    portfolio_snapshot: Dict[str, Any] = {}
    if portfolio_manager:
        try:
            portfolio_snapshot = portfolio_manager.get_portfolio_summary()
        except Exception as exc:
            logger.error(f"Failed to gather portfolio metrics: {exc}")

    uptime_seconds = int((datetime.now() - APP_START_TIME).total_seconds())

    cache_status = None
    if cache_manager and hasattr(cache_manager, "health_check"):
        try:
            cache_status = cache_manager.health_check()
        except Exception:
            cache_status = False

    cache_health = "unknown"
    if cache_status is True:
        cache_health = "healthy"
    elif cache_status is False:
        cache_health = "unhealthy"

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_seconds,
        "logger_metrics": telemetry,
        "portfolio": portfolio_snapshot,
        "trade_stream": {
            "subscribers": await trade_stream_manager.count_subscribers()
        },
        "dependencies": {
            "cache": cache_health
        },
        "trading": {
            "uptime_seconds": uptime_seconds,
            "trade_stream": {
                "subscribers": await trade_stream_manager.count_subscribers()
            }
        },
        "system": {
            "logger_metrics": telemetry,
            "dependencies": {
                "cache": cache_health
            }
        }
    }
    return metrics

# API router providing namespaced endpoints
api_router = APIRouter(prefix="/api", tags=["api"])


@api_router.get("/health")
async def api_health():
    return await get_health()


@api_router.get("/status")
async def api_status():
    return await get_status()


@api_router.get("/metrics")
async def api_metrics():
    return await get_metrics()


@api_router.get("/portfolio")
async def api_portfolio():
    return await get_portfolio()


@api_router.get("/positions")
async def api_positions():
    return await get_positions()

@api_router.get("/orders/recent")
async def api_orders_recent(limit: int = 50):
    return await get_recent_orders(limit=limit)


@api_router.post("/trades")
async def api_trades(trade: TradeRequest, current_user: Dict = Depends(get_current_active_user)):
    return await place_trade(trade, current_user)


@api_router.post("/strategy/start")
async def api_strategy_start(strategy_name: str):
    return await manage_strategy("activate", strategy_name)


@api_router.post("/strategy/stop")
async def api_strategy_stop(strategy_name: str):
    return await manage_strategy("deactivate", strategy_name)


@api_router.get("/logs")
async def api_logs(
    level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    current_admin: Dict = Depends(get_current_admin_user),
):
    return await get_logs(level=level, limit=limit, since=since, until=until, current_admin=current_admin)


@api_router.websocket("/ws/dashboard")
async def api_ws_dashboard(websocket: WebSocket):
    await websocket_dashboard(websocket)


app.include_router(api_router)

@app.get("/protected")
async def protected_endpoint(current_user: Dict = Depends(get_current_active_user)):
    """Protected endpoint example."""
    return {"message": f"Hello {current_user['username']}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
