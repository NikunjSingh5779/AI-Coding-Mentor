"""Canonical diagnostic protocol models."""

from enum import Enum
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
    line: int = Field(..., ge=1)
    col: int = Field(..., ge=1)


class DiagnosticRange(BaseModel):
    start: Position
    end: Position


class Diagnostic(BaseModel):
    id: str
    seq: int = 0
    origin: Origin
    rule: str | None = None
    category: str
    severity: Severity
    message_raw: str
    range: DiagnosticRange
    fingerprint: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
