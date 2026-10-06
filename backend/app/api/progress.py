"""Progress API: metrics from the learner tracker and per-session history."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.learner import repositories as repo
from app.learner.adaptation import build_profile
from app.learner.tracking import get_tracker

router = APIRouter()


@router.get("/progress/{session_token}")
async def progress(session_token: str) -> dict[str, Any]:
    tracker = get_tracker(session_token)
    summary = tracker.summary()
    profile = build_profile(
        [
            {"category": r.category, "resolved": r.is_resolved}
            for r in tracker.issues.values()
        ]
    )
    return {
        **summary,
        "adaptation": {
            "recurring_categories": profile.recurring_categories,
            "suggested_starting_level": profile.suggested_starting_level,
            "summary": profile.summary_for_prompt,
        },
    }


@router.get("/progress")
async def progress_overview(db: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    sessions = await repo.list_sessions(db, limit=50)
    total_sessions = len(sessions)
    total_hints = sum(s.get("total_hints_requested", 0) or 0 for s in sessions)
    return {
        "sessions": sessions,
        "totals": {
            "sessions": total_sessions,
            "hints_requested": total_hints,
        },
    }
