"""
DreamXV AI Studio — WebSocket Handler
======================================
Real-time agent status updates via WebSocket at /ws/status.
"""

from __future__ import annotations

import json
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from backend.models.schemas import AgentStatus
from backend.utils.logger import get_logger

logger = get_logger("websocket")


class ConnectionManager:
    """Manages active WebSocket connections for status broadcasting."""

    def __init__(self) -> None:
        self._active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active: {len(self._active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected WebSocket."""
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Active: {len(self._active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """Broadcast a JSON message to all connected clients."""
        disconnected = []
        for connection in self._active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn)

    def create_status_callback(self):
        """
        Create a synchronous callback that can be passed to BandManager.

        The callback wraps the async broadcast in a fire-and-forget manner
        compatible with the sync status update path.
        """
        import asyncio

        def callback(
            project_id: str,
            agent_name: str,
            status: AgentStatus,
            message: Optional[str] = None,
        ) -> None:
            payload = {
                "type": "agent_status",
                "project_id": project_id,
                "agent_name": agent_name,
                "status": status.value,
                "message": message,
            }

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.broadcast(payload))
            except RuntimeError:
                # No running loop — skip broadcast
                pass

        return callback


# Global connection manager instance
ws_manager = ConnectionManager()


async def websocket_status_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint handler for /ws/status.

    Clients connect to receive real-time agent status updates.
    The connection stays open until the client disconnects.
    """
    await ws_manager.connect(websocket)

    try:
        # Keep connection alive — listen for any client messages
        while True:
            data = await websocket.receive_text()
            # Echo back acknowledgment (clients can send pings)
            await websocket.send_json({
                "type": "ack",
                "message": f"Received: {data}",
            })
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning(f"WebSocket error: {exc}")
        ws_manager.disconnect(websocket)
