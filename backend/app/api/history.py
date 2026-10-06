"""History API: the learner's record of sessions, issues and delete-my-data."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.learner import repositories as repo
from app.learner.tracking import get_tracker

router = APIRouter()


@router.get("/history/sessions")
async def list_sessions(limit: int = 50, db: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    sessions = await repo.list_sessions(db, limit=limit)
    return {"sessions": sessions}


@router.get("/history/{session_token}/issues")
async def session_issues(session_token: str, db: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    session = await repo.get_session_by_token(db, session_token)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    issues = await repo.session_issue_history(db, session_token)
    tracker = get_tracker(session_token)
    return {
        "session_token": session_token,
        "db_records": issues,
        "live_summary": tracker.summary(),
    }


@router.get("/history/{session_token}/summary")
async def session_summary(session_token: str) -> dict[str, Any]:
    tracker = get_tracker(session_token)
    return tracker.summary()


@router.delete("/history/{session_token}")
async def delete_my_data(session_token: str, db: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    """Delete-my-data: removes the session, its issues, hints and checkpoints."""
    ok = await repo.delete_session_data(db, session_token)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted", "session_token": session_token}
