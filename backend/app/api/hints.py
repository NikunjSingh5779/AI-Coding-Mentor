"""Hint API: request hints from the mentor engine and give feedback."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.mentor.engine import MentorEngine
from app.mentor.llm.registry import get_llm_provider

logger = get_logger(__name__)

router = APIRouter()

# Single-process, single-user app (Q5): one engine instance is enough.
_engine: MentorEngine | None = None
# Latest code/diagnostics per session token (in-memory, latest-wins).
_last_code: dict[str, str] = {}
_last_diags: dict[str, list[dict[str, Any]]] = {}


def get_engine() -> MentorEngine:
    global _engine
    if _engine is None:
        _engine = MentorEngine()
    return _engine


def reset_engine() -> None:
    """Reset engine state (used by tests)."""
    global _engine
    _engine = None
    _last_code.clear()
    _last_diags.clear()


def record_analysis_context(session_token: str, code: str, diagnostics: list[dict[str, Any]]) -> None:
    """Called by the analysis flow so hints have the current context."""
    _last_code[session_token] = code
    _last_diags[session_token] = diagnostics


class HintRequestBody(BaseModel):
    issue_id: str
    level: int | None = Field(default=None, ge=1, le=4)
    confirmed: bool = False


@router.post("/hints/{session_token}")
async def request_hint(session_token: str, body: HintRequestBody) -> dict[str, Any]:
    """Request a hint for one issue in this session."""
    code = _last_code.get(session_token, "")
    diagnostics = _last_diags.get(session_token, [])

    # The issue must exist in the current context (prevents hinting on stale ids).
    engine = get_engine()
    known = {d.get("fingerprint") or d.get("id") for d in diagnostics}
    if body.issue_id not in known and body.issue_id not in engine._issues:
        raise HTTPException(status_code=404, detail="Issue not found in the current snapshot")

    t0 = time.perf_counter()
    hint, notice = await engine.generate_hint(
        issue_id=body.issue_id,
        level=body.level,
        code=code,
        diagnostics=diagnostics,
        confirmed=body.confirmed,
    )
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    if hint is None:
        return {"hint": None, "notice": notice, "latency_ms": latency_ms}

    return {
        "hint": hint.model_dump(),
        "notice": notice,
        "latency_ms": latency_ms,
    }


@router.get("/hints/status")
async def mentor_status() -> dict[str, Any]:
    """LLM readiness for the frontend banner / fallback notice."""
    provider = get_llm_provider()
    return {
        "llm_enabled": (await provider.is_ready()) if provider.name != "disabled" else False,
        "provider": provider.name,
        "model": getattr(provider, "_model", None),
    }


@router.post("/hints/{hint_id}/feedback")
async def hint_feedback(hint_id: str, helpful: bool, reaction: str | None = None) -> dict[str, Any]:
    """Record hint feedback (logged; persisted per-learner in PH5)."""
    logger.info(
        "Hint feedback received",
        extra={"hint_id": hint_id, "helpful": helpful, "reaction": reaction},
    )
    return {"status": "recorded"}
