"""
API Router for Problem Bank and Code Execution endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.execution.client import SandboxClient
from app.execution.test_runner import TestRunner
from app.problems.store import ProblemStore, get_problem_store
from app.schemas.problem import Problem, ProblemSummary
from app.schemas.run import RunRequest, RunResult

router = APIRouter()


class CodeSubmissionRequest(BaseModel):
    """Request to submit code against a problem's test suite."""
    code: str = Field(..., description="Source code solution")
    language: str = Field(default="python", description="Programming language")


# Global instances
sandbox_client = SandboxClient()
test_runner = TestRunner(sandbox_client)


@router.get("/problems", response_model=List[ProblemSummary])
async def list_problems(store: ProblemStore = Depends(get_problem_store)):
    """List all available practice coding problems."""
    return store.list_problems()


@router.get("/problems/{problem_id}", response_model=Problem)
async def get_problem(problem_id: str, store: ProblemStore = Depends(get_problem_store)):
    """
    Retrieve problem details and starter code.
    Hidden test cases have their expected outputs redacted.
    """
    problem = store.get_problem(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem '{problem_id}' not found",
        )
    return problem.sanitized_for_client()


@router.post("/problems/{problem_id}/run", response_model=RunResult)
async def run_problem_code(
    problem_id: str,
    request: RunRequest,
    store: ProblemStore = Depends(get_problem_store),
):
    """Run problem solution code against custom standard input."""
    problem = store.get_problem(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem '{problem_id}' not found",
        )

    return await sandbox_client.run_code(
        code=request.code,
        language=request.language,
        stdin=request.stdin,
        timeout_seconds=problem.timeout_seconds,
    )


@router.post("/problems/{problem_id}/submit", response_model=RunResult)
async def submit_problem_code(
    problem_id: str,
    submission: CodeSubmissionRequest,
    store: ProblemStore = Depends(get_problem_store),
):
    """
    Evaluate code solution against all problem test cases (public and hidden).
    Hidden test cases report pass/fail only.
    """
    problem = store.get_problem(problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problem '{problem_id}' not found",
        )

    return await test_runner.run_problem_tests(
        problem=problem,
        code=submission.code,
        language=submission.language,
        include_hidden=True,
    )


@router.post("/run", response_model=RunResult)
async def execute_freeform_code(request: RunRequest):
    """Execute arbitrary freeform learner code in the sandbox."""
    return await sandbox_client.run_code(
        code=request.code,
        language=request.language,
        stdin=request.stdin,
        timeout_seconds=request.timeout_seconds or 5.0,
    )
