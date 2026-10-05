"""
Schemas for code execution and test runner results.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.diagnostic import Diagnostic


class TestCaseSpec(BaseModel):
    """Specification of a test case."""
    id: str
    stdin: str = ""
    expected_output: Optional[str] = None
    is_hidden: bool = False


class TestCaseResult(BaseModel):
    """Result of running a test case."""
    id: str
    passed: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    is_hidden: bool = False
    error_type: Optional[str] = None


class RunRequest(BaseModel):
    """Request to execute learner code."""
    code: str = Field(..., description="Source code to execute")
    language: str = Field(default="python", description="Programming language")
    stdin: str = Field(default="", description="Standard input for the program")
    problem_id: Optional[str] = Field(default=None, description="Optional problem ID to run tests for")
    timeout_seconds: Optional[float] = Field(default=5.0, description="Execution timeout limit in seconds")


class RunResult(BaseModel):
    """Result returned to the frontend / client from code execution."""
    status: str = Field(..., description="Overall status: success, error, timeout, memory_limit, busy, disabled")
    exit_code: int = Field(default=0, description="Process exit code")
    stdout: str = Field(default="", description="Captured standard output")
    stderr: str = Field(default="", description="Captured standard error")
    duration_ms: float = Field(default=0.0, description="Execution wall-clock duration in milliseconds")
    truncated: bool = Field(default=False, description="Whether output was truncated due to size limit")
    diagnostics: List[Diagnostic] = Field(default_factory=list, description="Extracted runtime diagnostics")
    test_results: Optional[List[TestCaseResult]] = Field(default=None, description="Results of problem test cases")
    all_passed: Optional[bool] = Field(default=None, description="True if all test cases passed")
