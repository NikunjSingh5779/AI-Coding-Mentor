"""Hint API: request hints from the mentor engine and give feedback."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.limits import hint_rate_limiter
from app.core.logging import get_logger
from app.learner.tracking import get_tracker
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


def _normalize_diagnostics(diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Give every diagnostic a stable id.

    The frontend identifies issues as `fingerprint`, falling back to
    `category:line:column`. We must derive the SAME id here, otherwise the
    hint ladder would treat each request as a brand-new issue and never
    progress past H1.
    """
    normalized: list[dict[str, Any]] = []
    for d in diagnostics:
        item = dict(d)
        if not item.get("fingerprint") and not item.get("id"):
            line = item.get("line")
            if line is None:
                line = ((item.get("range") or {}).get("start") or {}).get("line", 1)
            col = item.get("column")
            if col is None:
                col = ((item.get("range") or {}).get("start") or {}).get("col", 1)
            item["fingerprint"] = f"{item.get('category', 'UNKNOWN')}:{line}:{col}"
        normalized.append(item)
    return normalized


class HintRequestBody(BaseModel):
    issue_id: str
    level: int | None = Field(default=None, ge=1, le=4)
    confirmed: bool = False
    # The frontend sends the snapshot it already holds so the mentor works on
    # exactly the code the learner is looking at (no duplicated analysis state).
    code: str = ""
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/hints/{session_token}")
async def request_hint(session_token: str, body: HintRequestBody) -> dict[str, Any]:
    """Request a hint for one issue in this session."""
    if not hint_rate_limiter.allow(session_token):
        raise HTTPException(status_code=429, detail="Too many hint requests; slow down.")

    # Prefer the snapshot sent with the request; fall back to the last known one.
    if body.code or body.diagnostics:
        record_analysis_context(session_token, body.code, _normalize_diagnostics(body.diagnostics))
    code = _last_code.get(session_token, "")
    diagnostics = _last_diags.get(session_token, [])

    # Track the issues in this snapshot so the ladder has state to advance,
    # and feed the learner record (progress/history read from the tracker).
    engine = get_engine()
    engine.track_issues(seq=0, diagnostics=diagnostics)
    get_tracker(session_token).observe_diagnostics(diagnostics)

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

    # Count the hint against the issue so progress/history reflect real usage.
    get_tracker(session_token).record_hint_shown(body.issue_id, hint.level)

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
