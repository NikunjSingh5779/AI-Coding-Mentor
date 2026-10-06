from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db_session
from app.execution.sandbox import SandboxClient, SandboxUnavailable
from app.execution.service import ExecutionService
from app.models.session import CodeAnalysis
from app.persistence.service import get_session
from app.problems.problem_bank import get_problem
from app.schemas.api import ExecuteRequest, ProblemTestRequest

router = APIRouter(prefix="/execution", tags=["execution"])


def get_execution_service() -> ExecutionService:
    settings = get_settings()
    return ExecutionService(
        SandboxClient(
            settings.sandbox_url,
            timeout=settings.sandbox_max_timeout + 5,
            max_code_bytes=settings.max_code_bytes,
            secret=settings.sandbox_secret,
        )
    )


@router.post("/run")
async def run_code(
    request: ExecuteRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    settings = get_settings()
    if not settings.execution_enabled:
        raise HTTPException(503, "Execution is disabled")

    session = await get_session(db, request.session_token)
    if session is None:
        raise HTTPException(404, "Session not found")

    try:
        result = await get_execution_service().run(
            request.code,
            request.language,
            request.stdin,
            request.timeout,
        )
    except SandboxUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc

    db.add(
        CodeAnalysis(
            session_id=session.id,
            analysis_type="execution",
            analyzer_name="sandbox",
            code_snapshot=request.code if settings.store_code_text else None,
            code_hash=hashlib.sha256(request.code.encode("utf-8")).hexdigest(),
            findings=result,
            severity="info" if result["success"] else "error",
            is_blocking=not result["success"],
        )
    )
    return result


@router.post("/test")
async def run_problem_tests(
    request: ProblemTestRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    settings = get_settings()
    if not settings.execution_enabled:
        raise HTTPException(503, "Execution is disabled")

    session = await get_session(db, request.session_token)
    if session is None:
        raise HTTPException(404, "Session not found")

    problem = get_problem(request.problem_id)
    if problem is None:
        raise HTTPException(404, "Problem not found")

    try:
        result = await get_execution_service().run_problem_tests(
            request.code,
            problem,
            request.language.lower(),
        )
    except SandboxUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc

    db.add(
        CodeAnalysis(
            session_id=session.id,
            analysis_type="tests",
            analyzer_name="sandbox",
            code_snapshot=request.code if settings.store_code_text else None,
            code_hash=hashlib.sha256(request.code.encode("utf-8")).hexdigest(),
            findings=result,
            severity="info" if result["passed"] else "error",
            is_blocking=not result["passed"],
        )
    )
    return result
