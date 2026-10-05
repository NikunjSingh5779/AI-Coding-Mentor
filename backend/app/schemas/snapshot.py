"""
CodeSnapshot Schema definitions.
Follows 03-ARCHITECTURE.md section 6.3.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SnapshotSource(str, Enum):
    EDITOR = "editor"
    SCREEN = "screen"
    EXTENSION = "extension"


class SnapshotLanguage(str, Enum):
    PYTHON = "python"
    CPP = "cpp"
    JAVA = "java"
    UNKNOWN = "unknown"


class CursorPosition(BaseModel):
    line: int = Field(default=1, ge=1)
    col: int = Field(default=1, ge=1)


class CodeSnapshot(BaseModel):
    seq: int = Field(default=0, ge=0)
    source: SnapshotSource = SnapshotSource.EDITOR
    language: SnapshotLanguage = SnapshotLanguage.PYTHON
    content: str
    cursor: Optional[CursorPosition] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    captured_at: Optional[str] = None
