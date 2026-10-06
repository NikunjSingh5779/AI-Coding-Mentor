from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db_session
from app.mentor.service import MentorService
from app.models.session import CodeAnalysis
from app.persistence.service import get_session
from app.schemas.api import HintRequest, HintFeedbackRequest

router = APIRouter(prefix="/mentor", tags=["mentor"])


@router.post("/hint")
async def request_hint(
    request: HintRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    session = await get_session(db, request.session_token)
    if session is None:
        raise HTTPException(404, "Session not found")

    analysis = None
    if request.analysis_id is not None:
        analysis = await db.get(CodeAnalysis, request.analysis_id)
        if analysis is None or analysis.session_id != session.id:
            raise HTTPException(404, "Analysis not found")

    try:
        return await MentorService(get_settings()).request_hint(
            db,
            session=session,
            analysis=analysis,
            requested_level=request.hint_level,
            allow_solution=request.allow_solution,
        )
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/hint/{hint_id}/feedback")
async def hint_feedback(
    hint_id: int,
    request: HintFeedbackRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, bool]:
    session = await get_session(db, request.session_token)
    if session is None:
        raise HTTPException(404, "Session not found")
    from app.models.session import MentorHint
    hint = await db.get(MentorHint, hint_id)
    if hint is None or hint.session_id != session.id:
        raise HTTPException(404, "Hint not found")

    allowed = {"helpful", "confusing", "incorrect", "too_advanced", "too_simple"}
    if request.reaction and request.reaction not in allowed:
        raise HTTPException(400, "Invalid reaction")

    hint.was_helpful = request.was_helpful
    hint.user_reaction = request.reaction
    return {"recorded": True}
