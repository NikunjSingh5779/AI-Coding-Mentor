"""
Complete Analysis Controller with Multi-Provider AI Integration
"""

import hashlib
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..analysis.python_analyzer import analyzer
from ..core.database import get_db_session
from ..models.session import CodeAnalysis, CodingSession
from ..views.session_views import AnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze")
async def analyze_code(
    session_token: str,
    code: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Complete code analysis pipeline with Python AST parsing, linting, and execution
    """

    # Verify session exists
    session_query = select(CodingSession).where(
        CodingSession.session_token == session_token, CodingSession.is_active == True
    )
    session = await db.scalar(session_query)

    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # Calculate code hash for deduplication
    code_hash = hashlib.sha256(code.encode()).hexdigest()

    # Check if we've already analyzed this exact code
    existing_analysis = await db.scalar(
        select(CodeAnalysis).where(
            CodeAnalysis.session_id == session.id, CodeAnalysis.code_hash == code_hash
        )
    )

    if existing_analysis:
        return {
            "cached": True,
            "analysis_id": existing_analysis.id,
            "findings": existing_analysis.findings,
            "severity": existing_analysis.severity,
        }

    # Run complete Python analysis
    try:
        analysis_results = analyzer.analyze(code)

        # Determine overall severity
        severity = "info"
        if analysis_results["syntax_errors"]:
            severity = "error"
        elif analysis_results["execution_result"]["error"]:
            severity = "error"
        elif len(analysis_results["diagnostics"]) > 5:
            severity = "warning"

        # Create analysis record
        new_analysis = CodeAnalysis(
            session_id=session.id,
            analysis_type="complete_python",
            analyzer_name="python_analyzer",
            code_snapshot=code,
            code_hash=code_hash,
            findings=analysis_results,
            severity=severity,
            is_blocking=(severity == "error"),
        )

        db.add(new_analysis)

        # Update session with latest code
        session.current_code = code

        await db.commit()
        await db.refresh(new_analysis)

        logger.info(f"Analysis complete for session {session.id}: {severity}")

        return {
            "cached": False,
            "analysis_id": new_analysis.id,
            "findings": analysis_results,
            "severity": severity,
            "is_blocking": new_analysis.is_blocking,
            "diagnostics_count": len(analysis_results["diagnostics"]),
        }

    except Exception as e:
        logger.error(f"Analysis failed for session {session.id}: {e}")

        # Create error analysis record
        error_analysis = CodeAnalysis(
            session_id=session.id,
            analysis_type="analysis_error",
            analyzer_name="python_analyzer",
            code_snapshot=code,
            code_hash=code_hash,
            findings={"error": str(e), "type": "analysis_failure"},
            severity="critical",
            is_blocking=True,
        )

        db.add(error_analysis)
        await db.commit()
        await db.refresh(error_analysis)

        return {
            "cached": False,
            "analysis_id": error_analysis.id,
            "findings": {"error": str(e)},
            "severity": "critical",
            "is_blocking": True,
            "error": f"Analysis failed: {str(e)}",
        }


@router.get("/analyses/{session_token}", response_model=list[AnalysisResponse])
async def get_analyses(
    session_token: str, db: AsyncSession = Depends(get_db_session)
) -> list[AnalysisResponse]:
    """Get all analyses for a session"""

    # Get session
    session_query = select(CodingSession).where(
        CodingSession.session_token == session_token
    )
    session = await db.scalar(session_query)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all analyses
    analyses_query = (
        select(CodeAnalysis)
        .where(CodeAnalysis.session_id == session.id)
        .order_by(CodeAnalysis.created_at.desc())
    )

    result = await db.execute(analyses_query)
    analyses = result.scalars().all()

    return [AnalysisResponse.from_orm(analysis) for analysis in analyses]


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, db: AsyncSession = Depends(get_db_session)):
    """Delete a specific analysis"""

    analysis = await db.get(CodeAnalysis, analysis_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    await db.delete(analysis)
    await db.commit()

    return {"message": "Analysis deleted successfully"}


@router.get("/health")
async def analysis_health():
    """Health check for analysis service"""
    try:
        # Test basic analysis
        test_code = "print('Hello, World!')"
        result = analyzer.analyze(test_code)

        return {
            "status": "healthy",
            "analyzer": "python_analyzer",
            "test_passed": True,
            "diagnostics_found": len(result["diagnostics"]),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "analyzer": "python_analyzer",
            "test_passed": False,
            "error": str(e),
        }
