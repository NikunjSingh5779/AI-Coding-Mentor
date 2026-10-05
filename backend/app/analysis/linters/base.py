"""
Base Linter Wrapper Interface.
"""

from abc import ABC, abstractmethod
from typing import List
from app.schemas.diagnostic import Diagnostic


class BaseLinter(ABC):
    """Abstract interface for static code linters."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if linter executable / library is available."""
        pass

    @abstractmethod
    def lint(self, code: str, filename: str = "snippet.py", seq: int = 0) -> List[Diagnostic]:
        """Run linter on code string and return diagnostics."""
        pass
