"""
Diagnostic Schema definitions.
Follows 03-ARCHITECTURE.md section 6.3.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUSPICION = "suspicion"


class Origin(str, Enum):
    TREESITTER = "treesitter"
    PARSER = "parser"
    LINTER = "linter"
    COMPILER = "compiler"
    RUNTIME = "runtime"
    TESTS = "tests"
    LLM = "llm"


class Position(BaseModel):
    line: int = Field(..., ge=1, description="1-indexed line number")
    col: int = Field(..., ge=1, description="1-indexed column offset")


class DiagnosticRange(BaseModel):
    start: Position
    end: Position


class Diagnostic(BaseModel):
    id: str
    seq: int = 0
    origin: Origin
    rule: Optional[str] = None
    category: str
    severity: Severity
    message_raw: str
    range: DiagnosticRange
    fingerprint: str
    confidence: float = 1.0
