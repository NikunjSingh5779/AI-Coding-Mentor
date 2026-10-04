"""
Mentor Controller - API endpoints for AI mentoring and hints
Following MVC pattern: Controllers handle request routing and business logic
"""

import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..models.session import CodeAnalysis, CodingSession, MentorHint
from ..views.session_views import HintResponse

router = APIRouter()


@router.post("/hints/request")
async def request_hint(
    session_token: str,
    analysis_id: int | None = None,
    hint_level: int = 1,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Request a hint for a coding issue
    This integrates with LLM providers to generate progressive hints
    """

    # Verify session exists
    session_query = select(CodingSession).where(
        CodingSession.session_token == session_token, CodingSession.is_active == True
    )
    session = await db.scalar(session_query)

    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # Validate hint level (H1-H4)
    if hint_level not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Hint level must be 1-4 (H1-H4)")

    # Verify analysis exists if provided
    analysis = None
    if analysis_id:
        analysis = await db.get(CodeAnalysis, analysis_id)
        if not analysis or analysis.session_id != session.id:
            raise HTTPException(
                status_code=404, detail="Analysis not found for this session"
            )

    # Check if H4 (solution) hint is being requested
    if hint_level == 4:
        # H4 requires explicit user confirmation (implemented in frontend)
        # For now, just log the request
        pass

    # TODO: Implement actual LLM integration
    # This will integrate with local/hosted LLM providers
    # For now, return a placeholder hint

    start_time = time.time()

    # Generate prompt hash for caching/dedup
    prompt_data = f"{session.current_code}{hint_level}{analysis_id}"
    prompt_hash = hashlib.sha256(prompt_data.encode()).hexdigest()

    # Check for existing hint with same prompt hash
    existing_hint = await db.scalar(
        select(MentorHint).where(
            MentorHint.session_id == session.id,
            MentorHint.prompt_hash == prompt_hash,
            MentorHint.hint_level == hint_level,
        )
    )

    if existing_hint:
        return {
            "cached": True,
            "hint_id": existing_hint.id,
            "hint_text": existing_hint.hint_text,
            "hint_level": existing_hint.hint_level,
        }

    # Placeholder hint generation
    generation_time_ms = int((time.time() - start_time) * 1000)

    hint_text = f"H{hint_level} hint: LLM integration not yet implemented. This would be a {'solution' if hint_level == 4 else 'progressive hint'} based on your code analysis."

    # Create hint record
    new_hint = MentorHint(
        session_id=session.id,
        analysis_id=analysis_id,
        hint_level=hint_level,
        hint_category="placeholder",
        hint_text=hint_text,
        hint_type="suggestion",
        llm_provider="placeholder",
        llm_model="placeholder-model",
        prompt_hash=prompt_hash,
        generation_time_ms=generation_time_ms,
        safety_approved=True,
        contains_solution=(hint_level == 4),
    )

    db.add(new_hint)

    # Update session metrics
    session.total_hints_requested += 1

    await db.commit()
    await db.refresh(new_hint)

    return {
        "cached": False,
        "hint_id": new_hint.id,
        "hint_text": new_hint.hint_text,
        "hint_level": new_hint.hint_level,
        "generation_time_ms": generation_time_ms,
    }


@router.get("/hints/{session_token}", response_model=list[HintResponse])
async def get_session_hints(
    session_token: str, db: AsyncSession = Depends(get_db_session)
) -> list[HintResponse]:
    """Get all hints for a session"""

    # Get session
    session_query = select(CodingSession).where(
        CodingSession.session_token == session_token
    )
    session = await db.scalar(session_query)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all hints
    hints_query = (
        select(MentorHint)
        .where(MentorHint.session_id == session.id)
        .order_by(MentorHint.created_at.desc())
    )

    result = await db.execute(hints_query)
    hints = result.scalars().all()

    return [HintResponse.from_orm(hint) for hint in hints]


@router.post("/hints/{hint_id}/feedback")
async def provide_feedback(
    hint_id: int,
    was_helpful: bool,
    reaction: str | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Provide feedback on a hint's helpfulness"""

    hint = await db.get(MentorHint, hint_id)

    if not hint:
        raise HTTPException(status_code=404, detail="Hint not found")

    # Valid reactions
    valid_reactions = [
        "helpful",
        "confusing",
        "incorrect",
        "too_advanced",
        "too_simple",
    ]

    if reaction and reaction not in valid_reactions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reaction. Must be one of: {', '.join(valid_reactions)}",
        )

    # Update hint feedback
    hint.was_helpful = was_helpful
    hint.user_reaction = reaction

    await db.commit()

    return {"message": "Feedback recorded successfully"}


@router.put("/hints/{hint_id}/mark-shown")
async def mark_hint_shown(hint_id: int, db: AsyncSession = Depends(get_db_session)):
    """Mark a hint as shown to the user (for analytics)"""

    hint = await db.get(MentorHint, hint_id)

    if not hint:
        raise HTTPException(status_code=404, detail="Hint not found")

    if not hint.shown_at:
        hint.shown_at = time.time()
        await db.commit()

    return {"message": "Hint marked as shown"}
