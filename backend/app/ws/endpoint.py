"""
Enhanced WebSocket endpoint for real-time code analysis and hint delivery.

Handles bidirectional communication between the frontend editor and the backend
analysis pipeline. Supports code snapshot submission, diagnostic delivery,
and hint request/response flow with comprehensive error handling and performance monitoring.
"""

import json
import time
import asyncio
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass, asdict

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from starlette.websockets import WebSocketState

from app.core.logging import get_logger
from app.analysis.python_analyzer import analyzer

logger = get_logger(__name__)


@dataclass
class WebSocketSession:
    """Represents an active WebSocket session with metadata."""
    session_token: str
    websocket: WebSocket
    connected_at: float
    last_ping: float
    sequence_number: int = 0
    language: str = "python"
    analysis_count: int = 0
    total_analysis_time: float = 0.0


class ConnectionManager:
    """Enhanced WebSocket connection manager with session tracking."""

    def __init__(self) -> None:
        self._sessions: Dict[str, WebSocketSession] = {}
        self._heartbeat_interval = 30.0  # 30 seconds
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(self, session_token: str, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection and create session."""
        # Validate origin (basic security check)
        origin = websocket.headers.get("origin", "")
        allowed_origins = {"http://localhost:5173", "http://127.0.0.1:5173"}

        if origin and origin not in allowed_origins:
            logger.warning(f"Rejected connection from unauthorized origin: {origin}")
            await websocket.close(code=1008, reason="Unauthorized origin")
            return

        await websocket.accept()

        now = time.time()
        session = WebSocketSession(
            session_token=session_token,
            websocket=websocket,
            connected_at=now,
            last_ping=now
        )

        # Clean up any existing session with same token
        if session_token in self._sessions:
            old_session = self._sessions[session_token]
            if old_session.websocket.client_state == WebSocketState.CONNECTED:
                await old_session.websocket.close(code=1000, reason="Duplicate session")

        self._sessions[session_token] = session

        # Start heartbeat task if this is the first connection
        if len(self._sessions) == 1 and not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info(
            "WebSocket connected",
            extra={
                "session_token": session_token,
                "origin": origin,
                "total_sessions": len(self._sessions)
            }
        )

    def disconnect(self, session_token: str) -> None:
        """Remove a session and clean up resources."""
        session = self._sessions.pop(session_token, None)
        if session:
            logger.info(
                "WebSocket disconnected",
                extra={
                    "session_token": session_token,
                    "session_duration": time.time() - session.connected_at,
                    "analysis_count": session.analysis_count,
                    "avg_analysis_time": (
                        session.total_analysis_time / session.analysis_count
                        if session.analysis_count > 0 else 0
                    ),
                    "remaining_sessions": len(self._sessions)
                }
            )

        # Stop heartbeat task if no more connections
        if not self._sessions and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def send_json(self, session_token: str, data: Dict[str, Any]) -> bool:
        """Send JSON message to a specific session."""
        session = self._sessions.get(session_token)
        if not session or session.websocket.client_state != WebSocketState.CONNECTED:
            return False

        try:
            await session.websocket.send_json(data)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to {session_token}: {e}")
            return False

    async def broadcast_json(self, data: Dict[str, Any]) -> int:
        """Broadcast JSON message to all connected sessions."""
        sent_count = 0
        for session_token in list(self._sessions.keys()):  # Copy to avoid mutation during iteration
            if await self.send_json(session_token, data):
                sent_count += 1
        return sent_count

    def get_session(self, session_token: str) -> Optional[WebSocketSession]:
        """Get session by token."""
        return self._sessions.get(session_token)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat pings to all connected clients."""
        try:
            while self._sessions:
                await asyncio.sleep(self._heartbeat_interval)

                current_time = time.time()
                disconnected_sessions = []

                for session_token, session in self._sessions.items():
                    # Check if session has been inactive too long
                    if current_time - session.last_ping > self._heartbeat_interval * 2:
                        disconnected_sessions.append(session_token)
                        continue

                    # Send ping
                    ping_sent = await self.send_json(session_token, {
                        "type": "ping",
                        "timestamp": current_time
                    })

                    if not ping_sent:
                        disconnected_sessions.append(session_token)

                # Clean up disconnected sessions
                for session_token in disconnected_sessions:
                    self.disconnect(session_token)

        except asyncio.CancelledError:
            logger.info("Heartbeat loop cancelled")
        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")

    @property
    def active_count(self) -> int:
        return len(self._sessions)

    @property
    def session_stats(self) -> Dict[str, Any]:
        """Get aggregated session statistics."""
        if not self._sessions:
            return {"active_sessions": 0}

        total_analysis_count = sum(s.analysis_count for s in self._sessions.values())
        total_analysis_time = sum(s.total_analysis_time for s in self._sessions.values())

        return {
            "active_sessions": len(self._sessions),
            "total_analysis_count": total_analysis_count,
            "avg_analysis_time": (
                total_analysis_time / total_analysis_count
                if total_analysis_count > 0 else 0
            ),
            "languages": list(set(s.language for s in self._sessions.values()))
        }


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, session_token: str = "anonymous") -> None:
    """
    Enhanced WebSocket endpoint for real-time code analysis sessions.

    Protocol messages (JSON):
        Client → Server:
            {"type": "code_update", "sequence": int, "code": str, "language": str, "timestamp": str}
            {"type": "ping", "timestamp": str}
            {"type": "pong", "timestamp": str}

        Server → Client:
            {"type": "analysis_result", "sequence": int, "diagnostics": [...], "analysis_time_ms": int, "timestamp": str}
            {"type": "ping", "timestamp": str}
            {"type": "pong", "timestamp": str}
            {"type": "error", "message": str, "code": str}
            {"type": "session_info", "session_token": str, "connected_at": str}
    """
    await manager.connect(session_token, websocket)

    try:
        # Send session info immediately after connection
        session = manager.get_session(session_token)
        if session:
            await websocket.send_json({
                "type": "session_info",
                "session_token": session_token,
                "connected_at": session.connected_at,
                "server_time": time.time()
            })

        while True:
            try:
                # Receive message with timeout
                raw_message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # 1 minute timeout
                )
            except asyncio.TimeoutError:
                # Send ping to check if connection is alive
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": time.time()
                })
                continue

            # Parse message
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Invalid JSON: {str(e)}",
                    "code": "INVALID_JSON"
                })
                continue

            # Validate message structure
            if not isinstance(message, dict) or "type" not in message:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message must be JSON object with 'type' field",
                    "code": "INVALID_MESSAGE"
                })
                continue

            message_type = message.get("type")

            # Handle different message types
            if message_type == "ping":
                session = manager.get_session(session_token)
                if session:
                    session.last_ping = time.time()
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": time.time()
                })

            elif message_type == "pong":
                session = manager.get_session(session_token)
                if session:
                    session.last_ping = time.time()

            elif message_type == "code_update":
                await handle_code_update(websocket, session_token, message)

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "code": "UNKNOWN_MESSAGE_TYPE"
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally: {session_token}")
    except asyncio.CancelledError:
        logger.info(f"WebSocket connection cancelled: {session_token}")
    except Exception as e:
        logger.exception(
            f"WebSocket error for session {session_token}: {str(e)}",
            extra={"session_token": session_token, "error": str(e)}
        )
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error",
                "code": "INTERNAL_ERROR"
            })
        except Exception:
            pass  # Connection might already be closed
    finally:
        manager.disconnect(session_token)


async def handle_code_update(websocket: WebSocket, session_token: str, message: Dict[str, Any]) -> None:
    """
    Handle code update message and perform real-time analysis.

    Args:
        websocket: WebSocket connection
        session_token: Session identifier
        message: Parsed message containing code and metadata
    """
    session = manager.get_session(session_token)
    if not session:
        await websocket.send_json({
            "type": "error",
            "message": "Session not found",
            "code": "SESSION_NOT_FOUND"
        })
        return

    # Validate required fields
    required_fields = ["sequence", "code", "language"]
    for field in required_fields:
        if field not in message:
            await websocket.send_json({
                "type": "error",
                "message": f"Missing required field: {field}",
                "code": "MISSING_FIELD"
            })
            return

    sequence = message.get("sequence", 0)
    code = message.get("code", "")
    language = message.get("language", "python")
    timestamp = message.get("timestamp", time.time())

    # Update session metadata
    session.sequence_number = max(session.sequence_number, sequence)
    session.language = language

    # Perform code analysis
    analysis_start = time.time()

    try:
        if language == "python":
            analysis_result = analyzer.analyze(code, max_time_ms=100)

            # Update session statistics
            session.analysis_count += 1
            session.total_analysis_time += analysis_result.get("analysis_time_ms", 0)

            # Send analysis result back to client
            response = {
                "type": "analysis_result",
                "sequence": sequence,
                "session_token": session_token,
                "diagnostics": analysis_result.get("diagnostics", []),
                "analysis_time_ms": analysis_result.get("analysis_time_ms", 0),
                "lines_of_code": analysis_result.get("lines_of_code", 0),
                "has_syntax_errors": analysis_result.get("has_syntax_errors", False),
                "performance": analysis_result.get("performance", {}),
                "timestamp": time.time(),
                "language": language
            }

            await websocket.send_json(response)

            # Log performance metrics
            if analysis_result.get("analysis_time_ms", 0) > 100:
                logger.warning(
                    "Slow analysis detected",
                    extra={
                        "session_token": session_token,
                        "analysis_time_ms": analysis_result.get("analysis_time_ms", 0),
                        "lines_of_code": analysis_result.get("lines_of_code", 0),
                        "diagnostic_count": len(analysis_result.get("diagnostics", []))
                    }
                )

        else:
            # Unsupported language
            await websocket.send_json({
                "type": "analysis_result",
                "sequence": sequence,
                "session_token": session_token,
                "diagnostics": [{
                    "line": 1,
                    "column": 0,
                    "message": f"Language '{language}' not yet supported. Python support available.",
                    "severity": "info",
                    "source": "language_support",
                    "category": "unsupported_language"
                }],
                "analysis_time_ms": 0,
                "timestamp": time.time(),
                "language": language
            })

    except Exception as e:
        logger.exception(f"Analysis error for {session_token}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": "Analysis failed",
            "code": "ANALYSIS_ERROR",
            "sequence": sequence
        })


# Export for main application
__all__ = ["manager", "websocket_endpoint", "WebSocketSession"]
