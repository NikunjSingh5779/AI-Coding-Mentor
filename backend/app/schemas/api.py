from __future__ import annotations

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    user_id: str = Field(default="local-user", min_length=1, max_length=255)
    language: str = Field(default="python", min_length=1, max_length=32)
    problem_id: str | None = None


class SessionResponse(BaseModel):
    id: int
    session_token: str
    user_id: str
    language: str
    problem_id: str | None
    is_active: bool


class ExecuteRequest(BaseModel):
    session_token: str
    code: str = Field(..., max_length=250_000)
    language: str = Field(default="python", min_length=1, max_length=32)
    stdin: str = Field(default="", max_length=50_000)
    timeout: int = Field(default=30, ge=1, le=60)


class ProblemTestRequest(BaseModel):
    session_token: str
    problem_id: str
    code: str = Field(..., max_length=250_000)
    language: str = "python"


class HintRequest(BaseModel):
    session_token: str
    analysis_id: int | None = None
    code: str = Field(default="", max_length=250_000)
    diagnostics: list[dict] = Field(default_factory=list)
    hint_level: int | None = Field(default=None, ge=1, le=4)
    allow_solution: bool = False


class HintFeedbackRequest(BaseModel):
    session_token: str
    was_helpful: bool
    reaction: str | None = None


class ScreenAnalysisResponse(BaseModel):
    session_token: str
    detected: bool
    confidence: float
    region: dict[str, int] | None
    code: str
    diagnostics: list[dict]
    notice: str | None = None


class CodeUpdateEnvelope(BaseModel):
    type: str
    sequence: int = Field(ge=0)
    code: str = Field(max_length=250_000)
    language: str = Field(default="python", max_length=32)
    timestamp: float | None = None
