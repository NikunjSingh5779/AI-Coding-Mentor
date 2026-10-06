"""WebSocket endpoint for real-time static code analysis."""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.analysis.pipeline import AnalysisPipeline
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WebSocketSession:
    session_token: str
    websocket: WebSocket
    connected_at: float
    last_activity: float
    sequence_number: int = 0
    language: str = "python"
    analysis_count: int = 0
    total_analysis_time: float = 0.0
    request_timestamps: deque[float] = None

    def __post_init__(self) -> None:
        if self.request_timestamps is None:
            self.request_timestamps = deque()


class ConnectionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, WebSocketSession] = {}
        settings = get_settings()
        self._heartbeat_interval = max(5, settings.ws_heartbeat_interval)
        self._max_message_size = max(1024, settings.ws_max_message_size)
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._analysis_semaphore: asyncio.Semaphore | None = None

    async def connect(self, session_token: str, websocket: WebSocket) -> bool:
        origin = websocket.headers.get("origin", "")
        allowed_origins = set(get_settings().cors_origins)

        if origin and origin not in allowed_origins:
            logger.warning("Rejected WebSocket origin", extra={"origin": origin})
            await websocket.close(code=1008, reason="Unauthorized origin")
            return False

        await websocket.accept()

        old = self._sessions.get(session_token)
        if old and old.websocket.client_state == WebSocketState.CONNECTED:
            try:
                await old.websocket.close(code=1000, reason="Duplicate session")
            except Exception:
                pass

        now = time.time()
        self._sessions[session_token] = WebSocketSession(
            session_token=session_token,
            websocket=websocket,
            connected_at=now,
            last_activity=now,
        )

        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        return True

    def disconnect(self, session_token: str) -> None:
        session = self._sessions.pop(session_token, None)
        if session:
            logger.info(
                "WebSocket disconnected",
                extra={
                    "session_token": session_token,
                    "analysis_count": session.analysis_count,
                },
            )
        if not self._sessions and self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    def get_session(self, session_token: str) -> WebSocketSession | None:
        return self._sessions.get(session_token)

    def allow_analysis(self, session: WebSocketSession) -> bool:
        limit = max(1, get_settings().max_requests_per_minute)
        now = time.time()
        while session.request_timestamps and now - session.request_timestamps[0] >= 60:
            session.request_timestamps.popleft()
        if len(session.request_timestamps) >= limit:
            return False
        session.request_timestamps.append(now)
        return True

    def analysis_semaphore(self) -> asyncio.Semaphore:
        if self._analysis_semaphore is None:
            self._analysis_semaphore = asyncio.Semaphore(max(1, get_settings().max_concurrent_runs))
        return self._analysis_semaphore

    async def send_json(self, session_token: str, data: dict[str, Any]) -> bool:
        session = self._sessions.get(session_token)
        if not session or session.websocket.client_state != WebSocketState.CONNECTED:
            return False
        try:
            await session.websocket.send_json(data)
            return True
        except Exception:
            self.disconnect(session_token)
            return False

    async def _heartbeat_loop(self) -> None:
        try:
            while self._sessions:
                await asyncio.sleep(self._heartbeat_interval)
                now = time.time()
                stale: list[str] = []
                for token, session in list(self._sessions.items()):
                    if now - session.last_activity > self._heartbeat_interval * 2:
                        stale.append(token)
                        continue
                    if not await self.send_json(
                        token, {"type": "ping", "timestamp": now}
                    ):
                        stale.append(token)
                for token in stale:
                    self.disconnect(token)
        except asyncio.CancelledError:
            return

    @property
    def active_count(self) -> int:
        return len(self._sessions)


manager = ConnectionManager()
pipeline = AnalysisPipeline()


def _error(message: str, code: str, sequence: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "error",
        "message": message,
        "code": code,
    }
    if sequence is not None:
        payload["sequence"] = sequence
    return payload


async def handle_code_update(
    websocket: WebSocket, session_token: str, message: dict[str, Any]
) -> None:
    session = manager.get_session(session_token)
    if not session:
        await websocket.send_json(_error("Session not found", "SESSION_NOT_FOUND"))
        return

    if "sequence" not in message or "code" not in message or "language" not in message:
        await websocket.send_json(
            _error("Missing required fields: sequence, code, language", "MISSING_FIELD")
        )
        return

    sequence = message["sequence"]
    code = message["code"]
    language = message["language"]

    if (
        not isinstance(sequence, int)
        or sequence < 0
        or not isinstance(code, str)
        or not isinstance(language, str)
    ):
        await websocket.send_json(_error("Invalid code_update payload", "INVALID_PAYLOAD"))
        return

    if len(json.dumps(message, ensure_ascii=False).encode("utf-8")) > manager._max_message_size:
        await websocket.send_json(_error("Message too large", "MESSAGE_TOO_LARGE", sequence))
        return

    # Only analyze the latest snapshot. Older queued messages must never overwrite
    # newer diagnostics.
    if sequence <= session.sequence_number:
        return

    if not manager.allow_analysis(session):
        await websocket.send_json(_error("Analysis rate limit exceeded", "RATE_LIMITED", sequence))
        return

    session.sequence_number = sequence
    session.language = language
    session.last_activity = time.time()

    started = time.perf_counter()
    async with manager.analysis_semaphore():
        diagnostics, stage_timings = await pipeline.analyze(code, language=language, seq=sequence)
    elapsed_ms = (time.perf_counter() - started) * 1000

    current = manager.get_session(session_token)
    if current is not session or sequence < session.sequence_number:
        return

    session.analysis_count += 1
    session.total_analysis_time += elapsed_ms

    diagnostics_payload = [
        {
            "id": d.id,
            "seq": d.seq,
            "origin": d.origin.value,
            "rule": d.rule,
            "category": d.category,
            "severity": d.severity.value,
            "message": d.message_raw,
            "range": {
                "start": {
                    "line": d.range.start.line,
                    "column": d.range.start.col,
                },
                "end": {
                    "line": d.range.end.line,
                    "column": d.range.end.col,
                },
            },
            "fingerprint": d.fingerprint,
            "confidence": d.confidence,
        }
        for d in diagnostics
    ]

    await websocket.send_json(
        {
            "type": "analysis_result",
            "sequence": sequence,
            "session_token": session_token,
            "diagnostics": diagnostics_payload,
            "analysis_time_ms": round(elapsed_ms, 2),
            "lines_of_code": len(code.splitlines()),
            "has_syntax_errors": any(
                d.severity.value == "error" and d.origin.value == "parser"
                for d in diagnostics
            ),
            "performance": {
                "within_budget": elapsed_ms <= 100,
                "diagnostic_count": len(diagnostics_payload),
            },
            "stage_timings": stage_timings,
            "timestamp": time.time(),
            "language": language,
        }
    )


async def websocket_endpoint(websocket: WebSocket, session_token: str = "anonymous") -> None:
    if not await manager.connect(session_token, websocket):
        return

    try:
        session = manager.get_session(session_token)
        if session:
            await websocket.send_json(
                {
                    "type": "session_info",
                    "session_token": session_token,
                    "connected_at": session.connected_at,
                    "server_time": time.time(),
                }
            )

        while True:
            try:
                raw = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=self_timeout := manager._heartbeat_interval,
                )
            except asyncio.TimeoutError:
                if manager.get_session(session_token):
                    await manager.send_json(
                        session_token, {"type": "ping", "timestamp": time.time()}
                    )
                continue

            if len(raw.encode("utf-8")) > manager._max_message_size:
                await websocket.send_json(_error("Message too large", "MESSAGE_TOO_LARGE"))
                continue

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(_error("Invalid JSON", "INVALID_JSON"))
                continue

            if not isinstance(message, dict) or not isinstance(message.get("type"), str):
                await websocket.send_json(
                    _error("Message must be a JSON object with a type field", "INVALID_MESSAGE")
                )
                continue

            message_type = message["type"]
            session = manager.get_session(session_token)
            if session:
                session.last_activity = time.time()

            if message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": time.time()})
            elif message_type == "pong":
                continue
            elif message_type == "code_update":
                await handle_code_update(websocket, session_token, message)
            else:
                await websocket.send_json(
                    _error(f"Unknown message type: {message_type}", "UNKNOWN_MESSAGE_TYPE")
                )

    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("WebSocket connection failed", extra={"session_token": session_token})
        try:
            await websocket.send_json(_error("Internal server error", "INTERNAL_ERROR"))
        except Exception:
            pass
    finally:
        manager.disconnect(session_token)


__all__ = ["manager", "pipeline", "websocket_endpoint", "WebSocketSession"]
