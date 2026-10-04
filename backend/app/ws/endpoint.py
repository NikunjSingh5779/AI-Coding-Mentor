"""
WebSocket endpoint for real-time code analysis and hint delivery.

Handles bidirectional communication between the frontend editor and the backend
analysis pipeline. Supports code snapshot submission, diagnostic delivery,
and hint request/response flow.
"""

import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per session."""

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id] = websocket
        logger.info("WebSocket connected", extra={"session_id": session_id})

    def disconnect(self, session_id: str) -> None:
        self._connections.pop(session_id, None)
        logger.info("WebSocket disconnected", extra={"session_id": session_id})

    async def send_json(self, session_id: str, data: dict[str, Any]) -> None:
        ws = self._connections.get(session_id)
        if ws:
            await ws.send_json(data)

    @property
    def active_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for real-time code analysis sessions.

    Protocol messages (JSON):
        Client → Server:
            {"type": "snapshot", "session_id": str, "sequence": int, "code": str, "language": str}
            {"type": "hint_request", "session_id": str, "issue_id": str, "level": int}
            {"type": "ping"}

        Server → Client:
            {"type": "diagnostics", "session_id": str, "sequence": int, "diagnostics": [...]}
            {"type": "hint", "session_id": str, "issue_id": str, "level": int, "text": str}
            {"type": "error", "message": str}
            {"type": "pong"}
    """
    session_id = websocket.query_params.get("session_id", "anonymous")

    await manager.connect(session_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = message.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "snapshot":
                # Acknowledge receipt; real analysis pipeline plugs in later.
                await websocket.send_json(
                    {
                        "type": "diagnostics",
                        "session_id": session_id,
                        "sequence": message.get("sequence", 0),
                        "diagnostics": [],
                    }
                )

            elif msg_type == "hint_request":
                # Stub response; mentor module plugs in later.
                await websocket.send_json(
                    {
                        "type": "hint",
                        "session_id": session_id,
                        "issue_id": message.get("issue_id", ""),
                        "level": message.get("level", 1),
                        "text": "Hint generation will be wired in a later phase.",
                    }
                )

            else:
                await websocket.send_json(
                    {"type": "error", "message": f"Unknown message type: {msg_type}"}
                )

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception:
        logger.exception("WebSocket error", extra={"session_id": session_id})
        manager.disconnect(session_id)
