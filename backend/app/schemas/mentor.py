from __future__ import annotations

from pydantic import BaseModel, Field


class MentorHintResponse(BaseModel):
    id: int
    hint_level: int
    hint_category: str
    hint_text: str
    hint_type: str
    provider: str
    model: str
    generation_time_ms: int | None
    safety_approved: bool
    contains_solution: bool
    created_at: str | None


class AnalyticsResponse(BaseModel):
    session_token: str
    analyses: int
    hints: int
    errors_detected: int
    errors_fixed: int
    execution_runs: int
    tests_passed: int
    tests_total: int
    avg_analysis_ms: float
    avg_execution_ms: float
    top_categories: list[dict[str, int]] = Field(default_factory=list)
