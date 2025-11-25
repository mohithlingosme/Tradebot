from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List

from .config import settings
from .database import create_db_and_tables
from .routes import router
from .routes_ai import router as ai_router
from .payments.routes import router as payments_router
from .routers import health, portfolio, positions, strategy, system, trades
from .sim import simulator
from .telemetry import RequestTimingMiddleware, configure_sentry
from .security.middleware import EnforceHTTPSMiddleware, SecurityHeadersMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="1.1.0")
# Run with: uvicorn backend.app.main:app --reload

configure_sentry()

# Add middleware
app.add_middleware(RequestTimingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(EnforceHTTPSMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(payments_router, prefix="/api")

# New layered routers
app.include_router(health.router)
app.include_router(system.router)
app.include_router(portfolio.router)
app.include_router(positions.router)
app.include_router(trades.router)
app.include_router(strategy.router)

# In-memory storage for demo purposes
# In production, use a proper database
market_data: Dict[str, Dict] = {}
connected_clients: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    create_db_and_tables()
    logger.info("Database initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/health")
async def api_health_check():
    """API-prefixed health check so frontend/curl can verify /api is reachable."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time market data."""
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        # Send initial data
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to market data stream"
        })

        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                if message.get("type") == "subscribe":
                    symbols = message.get("symbols", [])
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbols": symbols
                    })

                    # Start sending mock real-time data
                    asyncio.create_task(send_realtime_data(websocket, symbols))

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message"
                })

    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        logger.info("Client disconnected")

async def send_realtime_data(websocket: WebSocket, symbols: List[str]):
    """Send mock real-time market data."""
    while websocket in connected_clients:
        try:
            for symbol in symbols:
                # Generate mock price update using simulator
                update = simulator.generate_realtime_update(symbol)

                await websocket.send_json(update)

            await asyncio.sleep(1)  # Send updates every second

        except Exception as e:
            logger.error(f"Error sending real-time data: {e}")
            break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
