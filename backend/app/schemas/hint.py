"""Hint and mentor-output schemas (exported to TypeScript in later wiring)."""

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.diagnostic import Diagnostic


class HintSource(str, Enum):
    LLM = "llm"
    TEMPLATE = "template"
    CACHE = "cache"


class HintModel(BaseModel):
    """A mentor hint delivered to the frontend."""

    id: str
    issue_id: str
    level: int = Field(ge=1, le=4)
    text: str
    source: HintSource
    category: str
    created_at: str
    latency_ms: float = 0.0
    contains_solution: bool = False


class HintRequestModel(BaseModel):
    """Learner request for a hint on an issue."""

    issue_id: str
    level: int | None = Field(default=None, ge=1, le=4)
    confirmed: bool = False


class NoticeModel(BaseModel):
    """A non-diagnostic notice from the system (e.g. mentor unavailable)."""

    kind: str  # mentor_unavailable | budget_exhausted | capture_state | ...
    message: str
