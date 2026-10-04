"""
Analysis Controller - API endpoints for code analysis
Following MVC pattern: Controllers handle request routing and business logic
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import hashlib

from ..core.database import get_db_session
from ..models.session import CodeAnalysis, CodingSession
from ..views.session_views import AnalysisResponse

router = APIRouter()


@router.post("/analyze")
async def analyze_code(
    session_token: str,
    code: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Trigger code analysis for a session
    This endpoint will be called by the frontend when code changes
    """

    # Verify session exists
    session_query = select(CodingSession).where(
        CodingSession.session_token == session_token,
        CodingSession.is_active == True
    )
    session = await db.scalar(session_query)

    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # Calculate code hash for deduplication
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # Check if we've already analyzed this exact code
    existing_analysis = await db.scalar(
        select(CodeAnalysis).where(
            CodeAnalysis.session_id == session.id,
            CodeAnalysis.code_hash == code_hash
        )
    )

    if existing_analysis:
        return {
            "cached": True,
            "analysis_id": existing_analysis.id,
            "findings": existing_analysis.findings
        }

    # TODO: Implement actual analysis pipeline
    # This will integrate with parsers, linters, and sandbox execution
    # For now, return a placeholder response

    return {
        "cached": False,
        "message": "Analysis pipeline not yet implemented",
        "session_id": session.id,
        "code_hash": code_hash
    }


@router.get("/analyses/{session_token}", response_model=List[AnalysisResponse])
async def get_analyses(
    session_token: str,
    db: AsyncSession = Depends(get_db_session)
) -> List[AnalysisResponse]:
    """Get all analyses for a session"""

    # Get session
    session_query = select(CodingSession).where(
        CodingSession.session_token == session_token
    )
    session = await db.scalar(session_query)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all analyses
    analyses_query = select(CodeAnalysis).where(
        CodeAnalysis.session_id == session.id
    ).order_by(CodeAnalysis.created_at.desc())

    result = await db.execute(analyses_query)
    analyses = result.scalars().all()

    return [AnalysisResponse.from_orm(analysis) for analysis in analyses]


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a specific analysis"""

    analysis = await db.get(CodeAnalysis, analysis_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    await db.delete(analysis)
    await db.commit()

    return {"message": "Analysis deleted successfully"}