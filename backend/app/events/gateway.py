"""
Realtime Gateway for WebSocket connections.

Handles authentication, subscriptions, and event delivery to clients.
"""

import asyncio
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.core.security import get_current_user_ws
from backend.app.events.bus import get_event_bus
from backend.app.events.schemas import EventEnvelope

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_queues: Dict[str, asyncio.Queue] = {}
        self.last_seen: Dict[str, datetime] = {}
        self.user_connections: Dict[str, set] = defaultdict(set)

    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_queues[connection_id] = asyncio.Queue()
        self.last_seen[connection_id] = datetime.utcnow()
        self.user_connections[user_id].add(connection_id)

        # Subscribe to user-specific events
        event_bus = get_event_bus()
        user_queue = await event_bus.subscribe_user(user_id)

        # Start event forwarding task
        asyncio.create_task(self._forward_events(connection_id, user_queue))

        logger.info(f"Client connected: {connection_id} for user {user_id}")

    async def disconnect(self, connection_id: str, user_id: str):
        """Clean up a disconnected WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        if connection_id in self.connection_queues:
            queue = self.connection_queues[connection_id]
            await get_event_bus().unsubscribe(queue)
            del self.connection_queues[connection_id]

        if connection_id in self.last_seen:
            del self.last_seen[connection_id]

        if user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)

        logger.info(f"Client disconnected: {connection_id}")

    async def send_event(self, connection_id: str, event: EventEnvelope):
        """Send an event to a specific connection."""
        if connection_id not in self.active_connections:
            return

        websocket = self.active_connections[connection_id]
        try:
            await websocket.send_json(event.dict())
            self.last_seen[connection_id] = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to send event to {connection_id}: {e}")
            # Connection might be dead, clean it up
            await self.disconnect(connection_id, event.user_id)

    async def _forward_events(self, connection_id: str, user_queue: asyncio.Queue):
        """Forward events from the user's queue to the WebSocket."""
        try:
            while True:
                event = await user_queue.get()
                await self.send_event(connection_id, event)
                user_queue.task_done()
        except Exception as e:
            logger.error(f"Event forwarding failed for {connection_id}: {e}")

    async def heartbeat(self):
        """Send heartbeat to all active connections."""
        dead_connections = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json({"type": "heartbeat", "ts": datetime.utcnow().isoformat()})
                self.last_seen[connection_id] = datetime.utcnow()
            except Exception as e:
                logger.error(f"Heartbeat failed for {connection_id}: {e}")
                dead_connections.append(connection_id)

        # Clean up dead connections
        for connection_id in dead_connections:
            # We don't know the user_id here, so we need to find it
            for user_id, connections in self.user_connections.items():
                if connection_id in connections:
                    await self.disconnect(connection_id, user_id)
                    break

    def get_connection_stats(self) -> Dict[str, int]:
        """Get connection statistics."""
        return {
            "active_connections": len(self.active_connections),
            "unique_users": len(self.user_connections)
        }


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for realtime updates."""
    connection_id = f"ws_{asyncio.current_task().get_name()}_{id(websocket)}"

    try:
        # Authenticate user
        user = await get_current_user_ws(token, db)
        if not user:
            await websocket.close(code=1008)  # Policy violation
            return

        # Connect the client
        await manager.connect(websocket, str(user.id), connection_id)

        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "user_id": str(user.id),
            "ts": datetime.utcnow().isoformat()
        })

        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages with timeout
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30 second timeout
                )

                # Handle client messages (e.g., subscription updates)
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "ts": datetime.utcnow().isoformat()
                    })
                elif data.get("type") == "subscribe":
                    # Handle topic subscriptions if needed
                    pass

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({
                    "type": "ping",
                    "ts": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        await manager.disconnect(connection_id, str(user.id))


# Background task for heartbeat
async def start_heartbeat():
    """Start the heartbeat background task."""
    while True:
        await asyncio.sleep(30)  # Send heartbeat every 30 seconds
        await manager.heartbeat()


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager
