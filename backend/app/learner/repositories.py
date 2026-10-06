"""Repositories: the only module that runs learner-record queries.

Keeps SQLAlchemy access out of controllers and tracking logic.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import CodeAnalysis, CodingSession, MentorHint


async def get_session_by_token(db: AsyncSession, session_token: str) -> CodingSession | None:
    return await db.scalar(select(CodingSession).where(CodingSession.session_token == session_token))


async def create_session(db: AsyncSession, user_id: str, language: str = "python") -> CodingSession:
    import uuid

    session = CodingSession(user_id=user_id, session_token=str(uuid.uuid4()), language=language)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def end_session(db: AsyncSession, session_token: str) -> bool:
    from datetime import UTC, datetime

    session = await get_session_by_token(db, session_token)
    if not session:
        return False
    session.is_active = False
    session.ended_at = datetime.now(UTC)
    await db.commit()
    return True


async def delete_session_data(db: AsyncSession, session_token: str) -> bool:
    """Delete-my-data: remove a session and all its children."""
    session = await get_session_by_token(db, session_token)
    if not session:
        return False
    await db.execute(delete(MentorHint).where(MentorHint.session_id == session.id))
    await db.execute(delete(CodeAnalysis).where(CodeAnalysis.session_id == session.id))
    await db.delete(session)
    await db.commit()
    return True


async def list_sessions(db: AsyncSession, limit: int = 50) -> list[dict[str, Any]]:
    result = await db.execute(
        select(CodingSession).order_by(CodingSession.created_at.desc()).limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "session_token": s.session_token,
            "user_id": s.user_id,
            "language": s.language,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "is_active": s.is_active,
            "total_hints_requested": s.total_hints_requested,
            "errors_fixed": s.errors_fixed,
        }
        for s in sessions
    ]


async def session_issue_history(db: AsyncSession, session_token: str) -> list[dict[str, Any]]:
    """The learner's record of mistakes for one session."""
    result = await db.execute(
        select(CodeAnalysis)
        .where(CodeAnalysis.session_id == (await get_session_by_token(db, session_token)).id)
        .order_by(CodeAnalysis.created_at)
    )
    analyses = result.scalars().all()
    return [
        {
            "id": a.id,
            "analysis_type": a.analysis_type,
            "analyzer_name": a.analyzer_name,
            "findings": a.findings,
            "severity": a.severity,
            "is_resolved": a.is_resolved,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in analyses
    ]
