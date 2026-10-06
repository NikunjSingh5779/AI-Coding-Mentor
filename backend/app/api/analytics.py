from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.session import CodeAnalysis, CodingSession, MentorHint
from app.persistence.service import get_session

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/{session_token}")
async def analytics(
    session_token: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    session = await get_session(db, session_token)
    if session is None:
        raise HTTPException(404, "Session not found")

    analyses = list(
        (
            await db.execute(
                select(CodeAnalysis)
                .where(CodeAnalysis.session_id == session.id)
            )
        ).scalars()
    )
    hints = int(
        await db.scalar(
            select(func.count(MentorHint.id)).where(
                MentorHint.session_id == session.id
            )
        )
        or 0
    )
    categories: Counter[str] = Counter()
    total_analysis_ms = 0.0
    execution_runs = 0
    execution_ms = 0.0
    tests_passed = 0
    tests_total = 0
    errors_detected = 0

    for item in analyses:
        if isinstance(item.findings, list):
            for finding in item.findings:
                if isinstance(finding, dict):
                    category = finding.get("category")
                    if category:
                        categories[str(category)] += 1
                    if finding.get("severity") == "error":
                        errors_detected += 1
        if item.analysis_type == "execution":
            execution_runs += 1
            if isinstance(item.findings, dict):
                execution_ms += float(item.findings.get("execution_time_ms", 0))
        if item.analysis_type == "tests" and isinstance(item.findings, dict):
            tests_total += int(item.findings.get("test_count", 0))
            tests_passed += int(item.findings.get("passed_count", 0))
        if item.analysis_type == "fast_static":
            total_analysis_ms += float(item.analysis_time_ms or 0)

    return {
        "session_token": session_token,
        "analyses": len(analyses),
        "hints": hints,
        "errors_detected": errors_detected,
        "errors_fixed": session.errors_fixed,
        "execution_runs": execution_runs,
        "tests_passed": tests_passed,
        "tests_total": tests_total,
        "avg_analysis_ms": round(total_analysis_ms / max(1, len(analyses)), 2),
        "avg_execution_ms": round(execution_ms / max(1, execution_runs), 2),
        "top_categories": [
            {"category": key, "count": value}
            for key, value in categories.most_common(8)
        ],
    }
