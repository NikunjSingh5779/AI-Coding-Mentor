from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.session import CodingSession, CodeAnalysis, MentorHint
from app.schemas.api import CreateSessionRequest, SessionResponse
from app.persistence.service import get_session

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    token = secrets.token_urlsafe(32)
    session = CodingSession(
        user_id=request.user_id,
        session_token=token,
        language=request.language.lower(),
        problem_id=request.problem_id,
        is_active=True,
    )
    db.add(session)
    await db.flush()
    return SessionResponse(
        id=session.id,
        session_token=session.session_token,
        user_id=session.user_id,
        language=session.language,
        problem_id=session.problem_id,
        is_active=session.is_active,
    )


@router.get("/{session_token}", response_model=SessionResponse)
async def read_session(
    session_token: str,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    session = await get_session(db, session_token)
    if session is None:
        raise HTTPException(404, "Session not found")
    return SessionResponse(
        id=session.id,
        session_token=session.session_token,
        user_id=session.user_id,
        language=session.language,
        problem_id=session.problem_id,
        is_active=session.is_active,
    )


@router.delete("/{session_token}")
async def delete_session(
    session_token: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    session = await get_session(db, session_token)
    if session is None:
        raise HTTPException(404, "Session not found")
    await db.delete(session)
    return {"deleted": True}


@router.get("/{session_token}/analyses")
async def list_analyses(
    session_token: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    session = await get_session(db, session_token)
    if session is None:
        raise HTTPException(404, "Session not found")
    result = await db.execute(
        select(CodeAnalysis)
        .where(CodeAnalysis.session_id == session.id)
        .order_by(CodeAnalysis.created_at.desc())
        .limit(50)
    )
    return [
        {
            "id": item.id,
            "analysis_type": item.analysis_type,
            "severity": item.severity,
            "findings": item.findings,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in result.scalars()
    ]


@router.get("/{session_token}/hints")
async def list_hints(
    session_token: str,
    db: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    session = await get_session(db, session_token)
    if session is None:
        raise HTTPException(404, "Session not found")
    result = await db.execute(
        select(MentorHint)
        .where(MentorHint.session_id == session.id)
        .order_by(MentorHint.created_at.desc())
        .limit(50)
    )
    return [
        {
            "id": item.id,
            "hint_level": item.hint_level,
            "hint_category": item.hint_category,
            "hint_text": item.hint_text,
            "provider": item.llm_provider,
            "model": item.llm_model,
            "contains_solution": item.contains_solution,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in result.scalars()
    ]
