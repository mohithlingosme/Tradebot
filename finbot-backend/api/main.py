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

import logging
import os
from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from .auth import (
    UserCredentials, TokenResponse, authenticate_user,
    create_access_token, get_current_active_user
)
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

app = FastAPI(
    title="Finbot Trading API",
    description="API for Finbot autonomous trading system",
    version="1.0.0"
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
live_engine_config = LiveTradingConfig(
    mode=TradingMode.SIMULATION,
    symbols=["AAPL"],
    update_interval_seconds=5.0
) if LiveTradingConfig else None
live_trading_engine = LiveTradingEngine(
    config=live_engine_config,
    strategy_manager=strategy_manager,
    portfolio_manager=portfolio_manager
) if LiveTradingEngine else None

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
            "logger": "active" if logger_service else "inactive"
        }
    }

@app.get("/portfolio")
async def get_portfolio():
    """
    Get portfolio summary.

    Returns:
        Portfolio summary dictionary
    """
    if not portfolio_manager:
        raise HTTPException(status_code=503, detail="Portfolio manager not available")

    try:
        return portfolio_manager.get_portfolio_summary()
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/positions")
async def get_positions():
    """
    Get current positions.

    Returns:
        List of position dictionaries
    """
    if not portfolio_manager:
        raise HTTPException(status_code=503, detail="Portfolio manager not available")

    try:
        return portfolio_manager.get_position_summary()
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
async def get_logs(lines: int = 100):
    """
    Get recent log entries with structured parsing.

    Args:
        lines: Number of log lines to return

    Returns:
        List of structured log entries
    """
    try:
        import os
        import re
        import json
        log_file = "logs/finbot.log"

        if not os.path.exists(log_file):
            return {"logs": [], "message": "No log file found"}

        with open(log_file, 'r') as f:
            all_lines = f.readlines()

        # Get the last 'lines' entries
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        # Parse log entries with structured parsing
        log_entries = []
        for line in recent_lines:
            line = line.strip()
            if line:
                # Parse log line: timestamp - name - level - message
                match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - ([^-]+) - (.+)$', line)
                if match:
                    timestamp, logger_name, level, message = match.groups()

                    # Parse component from message: [component] actual_message
                    component_match = re.match(r'^\[([^\]]+)\]\s*(.+)$', message)
                    if component_match:
                        component = component_match.group(1)
                        actual_message = component_match.group(2)
                    else:
                        component = logger_name
                        actual_message = message

                    # Parse additional fields: | Data: json | Trace: id | Duration: ms
                    data = {}
                    trace_id = None
                    duration_ms = None

                    # Split by ' | ' to get additional fields
                    parts = actual_message.split(' | ')
                    actual_message = parts[0]

                    for part in parts[1:]:
                        if part.startswith('Data: '):
                            try:
                                data = json.loads(part[6:])  # Remove 'Data: '
                            except json.JSONDecodeError:
                                data = {'raw_data': part[6:]}
                        elif part.startswith('Trace: '):
                            trace_id = part[7:]  # Remove 'Trace: '
                        elif part.startswith('Duration: '):
                            try:
                                duration_ms = float(part[10:].replace('ms', ''))  # Remove 'Duration: ' and 'ms'
                            except ValueError:
                                duration_ms = None

                    log_entries.append({
                        "timestamp": timestamp,
                        "level": level,
                        "component": component,
                        "message": actual_message,
                        "data": data,
                        "trace_id": trace_id,
                        "duration_ms": duration_ms
                    })
                else:
                    # Fallback for unparseable lines
                    log_entries.append({
                        "timestamp": "unknown",
                        "level": "unknown",
                        "component": "unknown",
                        "message": line,
                        "data": {},
                        "trace_id": None,
                        "duration_ms": None
                    })

        return {"logs": log_entries, "total_lines": len(all_lines)}
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

    try:
        while True:
            # TODO: Implement real-time trade streaming
            # - Subscribe to trade events
            # - Send updates to connected clients

            # For now, send periodic status updates
            import asyncio
            await asyncio.sleep(5)

            status_data = {
                "type": "status",
                "timestamp": datetime.now().isoformat(),
                "message": "Connection active"
            }

            await websocket.send_json(status_data)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
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

    access_token = create_access_token(data={"sub": user.username})
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

        # TODO: Implement actual trade execution through broker integration
        # For now, simulate trade execution
        trade_result = {
            "id": f"trade_{datetime.now().timestamp()}",
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.price or 100.0,  # Mock price
            "timestamp": datetime.now().isoformat(),
            "status": "executed"
        }

        logger.info(f"Trade executed: {trade_result}")
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
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "strategy_manager": "healthy" if strategy_manager else "unhealthy",
            "portfolio_manager": "healthy" if portfolio_manager else "unhealthy",
            "logger": "healthy" if logger_service else "unhealthy",
            "trading_engine": "healthy" if live_trading_engine else "unhealthy"
        },
        "database": "healthy",  # TODO: Add actual DB health check
        "external_apis": "healthy"  # TODO: Add external API health checks
    }

    # Check if any service is unhealthy
    if any(status == "unhealthy" for status in health_status["services"].values()):
        health_status["status"] = "degraded"

    return health_status

@app.get("/metrics")
async def get_metrics():
    """
    Get system performance metrics.

    Returns:
        Performance metrics dictionary
    """
    # TODO: Implement actual metrics collection
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "trading": {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "win_rate": 0.0
        },
        "portfolio": {
            "total_value": 100000.0,
            "cash": 95000.0,
            "positions_value": 5000.0,
            "pnl": 0.0
        },
        "system": {
            "uptime_seconds": 3600,
            "memory_usage_mb": 150.5,
            "cpu_usage_percent": 25.3
        }
    }

    return metrics

@app.get("/protected")
async def protected_endpoint(current_user: Dict = Depends(get_current_active_user)):
    """Protected endpoint example."""
    return {"message": f"Hello {current_user['username']}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
