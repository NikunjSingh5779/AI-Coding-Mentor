"""
Session Views - Response models for API serialization
Following MVC pattern: Views define data presentation and API contracts
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request model for creating a new coding session"""

    user_id: str = Field(..., description="User identifier for session tracking")
    language: str = Field(
        default="python", description="Programming language for the session"
    )
    problem_id: str | None = Field(None, description="ID of the problem to work on")
    hint_level_preference: int = Field(
        default=1, ge=1, le=4, description="Preferred hint level (H1-H4)"
    )
    screen_mode_enabled: bool = Field(
        default=False, description="Enable screen capture mode"
    )
    auto_analysis_enabled: bool = Field(
        default=True, description="Enable automatic code analysis"
    )
    settings: dict[str, Any] | None = Field(
        None, description="Custom session settings"
    )


class UpdateSessionRequest(BaseModel):
    """Request model for updating session details"""

    current_code: str | None = Field(None, description="Latest code snapshot")
    hint_level_preference: int | None = Field(
        None, ge=1, le=4, description="Update hint level preference"
    )
    screen_mode_enabled: bool | None = Field(
        None, description="Toggle screen capture mode"
    )
    auto_analysis_enabled: bool | None = Field(
        None, description="Toggle automatic analysis"
    )
    settings: dict[str, Any] | None = Field(
        None, description="Update session settings"
    )
    is_active: bool | None = Field(
        None, description="Mark session as active/inactive"
    )


class SessionResponse(BaseModel):
    """Response model for session data"""

    id: int = Field(..., description="Session database ID")
    user_id: str = Field(..., description="User identifier")
    session_token: str = Field(..., description="Unique session token")
    language: str = Field(..., description="Programming language")
    problem_id: str | None = Field(None, description="Associated problem ID")

    # Timestamps
    created_at: datetime = Field(..., description="Session creation time")
    updated_at: datetime = Field(..., description="Last update time")
    ended_at: datetime | None = Field(None, description="Session end time")

    # Session state
    is_active: bool = Field(..., description="Whether session is active")
    current_code: str | None = Field(None, description="Latest code snapshot")

    # Settings
    hint_level_preference: int = Field(..., description="Preferred hint level")
    screen_mode_enabled: bool = Field(..., description="Screen capture mode status")
    auto_analysis_enabled: bool = Field(..., description="Auto analysis status")

    # Metrics
    total_hints_requested: int = Field(..., description="Total hints requested")
    errors_fixed: int = Field(..., description="Number of errors fixed")
    session_duration_minutes: int = Field(..., description="Session duration")

    # Flexible fields
    settings: dict[str, Any] | None = Field(None, description="Custom settings")
    metadata: dict[str, Any] | None = Field(None, description="Session metadata")

    class Config:
        from_attributes = True


class ProblemResponse(BaseModel):
    """Response model for problem data"""

    id: str = Field(..., description="Problem identifier")
    title: str = Field(..., description="Problem title")
    description: str = Field(..., description="Problem description")
    difficulty: str = Field(..., description="Problem difficulty level")
    category: str = Field(..., description="Problem category")

    # Test cases (filtered for security)
    test_cases: list[dict[str, Any]] = Field(..., description="Public test cases")
    starter_code: str | None = Field(None, description="Starter code template")

    # Metadata
    created_at: datetime = Field(..., description="Problem creation time")
    times_attempted: int = Field(..., description="Number of attempts")
    average_completion_time: int | None = Field(
        None, description="Average completion time in minutes"
    )

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    """Response model for code analysis results"""

    id: int = Field(..., description="Analysis ID")
    session_id: int = Field(..., description="Associated session ID")
    analysis_type: str = Field(..., description="Type of analysis performed")
    analyzer_name: str = Field(..., description="Name of the analyzer tool")

    # Analysis results
    findings: list[dict[str, Any]] = Field(..., description="Analysis findings")
    severity: str = Field(..., description="Severity level")
    is_blocking: bool = Field(..., description="Whether this blocks execution")

    # Status
    is_resolved: bool = Field(..., description="Whether issue is resolved")
    created_at: datetime = Field(..., description="Analysis timestamp")
    resolved_at: datetime | None = Field(None, description="Resolution timestamp")

    class Config:
        from_attributes = True


class HintResponse(BaseModel):
    """Response model for mentor hints"""

    id: int = Field(..., description="Hint ID")
    session_id: int = Field(..., description="Associated session ID")
    analysis_id: int | None = Field(None, description="Associated analysis ID")

    # Hint details
    hint_level: int = Field(..., description="Hint level (1-4)")
    hint_category: str = Field(..., description="Category of the hint")
    hint_text: str = Field(..., description="The hint content")
    hint_type: str = Field(..., description="Type of hint")

    # LLM metadata
    llm_provider: str = Field(..., description="LLM provider used")
    llm_model: str = Field(..., description="LLM model name")
    generation_time_ms: int | None = Field(
        None, description="Generation time in milliseconds"
    )

    # User feedback
    was_helpful: bool | None = Field(
        None, description="User feedback on helpfulness"
    )
    user_reaction: str | None = Field(None, description="User reaction to hint")

    # Timestamps
    created_at: datetime = Field(..., description="Hint creation time")
    shown_at: datetime | None = Field(
        None, description="When hint was shown to user"
    )

    # Safety
    safety_approved: bool = Field(..., description="Whether hint passed safety checks")
    contains_solution: bool = Field(
        ..., description="Whether hint contains full solution"
    )

    class Config:
        from_attributes = True
