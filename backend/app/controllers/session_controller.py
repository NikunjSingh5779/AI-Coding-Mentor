"""
Session Controller - API endpoints for managing coding sessions
Following MVC pattern: Controllers handle request routing and business logic
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..models.session import CodingSession, Problem
from ..views.session_views import (
    CreateSessionRequest,
    SessionResponse,
    UpdateSessionRequest,
)

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest, db: AsyncSession = Depends(get_db_session)
) -> SessionResponse:
    """Create a new coding session"""

    # Generate unique session token
    session_token = str(uuid.uuid4())

    # Verify problem exists if provided
    if request.problem_id:
        problem_query = select(Problem).where(Problem.id == request.problem_id)
        problem = await db.scalar(problem_query)
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

    # Create new session
    new_session = CodingSession(
        user_id=request.user_id,
        session_token=session_token,
        language=request.language,
        problem_id=request.problem_id,
        hint_level_preference=request.hint_level_preference,
        screen_mode_enabled=request.screen_mode_enabled,
        auto_analysis_enabled=request.auto_analysis_enabled,
        settings=request.settings,
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return SessionResponse.from_orm(new_session)


@router.get("/sessions/{session_token}", response_model=SessionResponse)
async def get_session(
    session_token: str, db: AsyncSession = Depends(get_db_session)
) -> SessionResponse:
    """Get session by token"""

    query = select(CodingSession).where(CodingSession.session_token == session_token)
    session = await db.scalar(query)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse.from_orm(session)


@router.put("/sessions/{session_token}", response_model=SessionResponse)
async def update_session(
    session_token: str,
    request: UpdateSessionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """Update session details"""

    query = select(CodingSession).where(CodingSession.session_token == session_token)
    session = await db.scalar(query)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update fields if provided
    if request.current_code is not None:
        session.current_code = request.current_code

    if request.hint_level_preference is not None:
        session.hint_level_preference = request.hint_level_preference

    if request.screen_mode_enabled is not None:
        session.screen_mode_enabled = request.screen_mode_enabled

    if request.auto_analysis_enabled is not None:
        session.auto_analysis_enabled = request.auto_analysis_enabled

    if request.settings is not None:
        session.settings = request.settings

    if request.is_active is not None:
        session.is_active = request.is_active
        if not request.is_active:
            session.ended_at = datetime.utcnow()

    session.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(session)

    return SessionResponse.from_orm(session)


@router.get("/sessions/{session_token}/analyses")
async def get_session_analyses(
    session_token: str, db: AsyncSession = Depends(get_db_session)
):
    """Get all analyses for a session"""

    # Verify session exists
    session_query = select(CodingSession).where(
        CodingSession.session_token == session_token
    )
    session = await db.scalar(session_query)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # This will be implemented with the analysis controller
    return {"analyses": [], "session_id": session.id}


@router.delete("/sessions/{session_token}")
async def delete_session(
    session_token: str, db: AsyncSession = Depends(get_db_session)
):
    """Delete a session and all related data"""

    query = select(CodingSession).where(CodingSession.session_token == session_token)
    session = await db.scalar(query)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    return {"message": "Session deleted successfully"}
