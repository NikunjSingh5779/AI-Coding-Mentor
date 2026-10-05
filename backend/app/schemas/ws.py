"""
WebSocket message envelope and payload models.
Follows 03-ARCHITECTURE.md section 6.1 and 6.2.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.snapshot import CodeSnapshot
from app.schemas.diagnostic import Diagnostic


class WSEnvelope(BaseModel):
    v: int = Field(default=0, description="Protocol version")
    type: str
    id: str
    session_id: str
    ts: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class FastAnalysisPayload(BaseModel):
    seq: int
    diagnostics: List[Diagnostic]
    stage_timings: Dict[str, float] = Field(default_factory=dict)
