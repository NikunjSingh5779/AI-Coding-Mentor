"""LLM provider abstraction for the mentor engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LLMResult:
    """A completion result from an LLM provider."""

    text: str
    model: str
    provider: str
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    metadata: dict = field(default_factory=dict)


class LLMError(Exception):
    """Raised when an LLM call fails after retries."""


class LLMUnavailable(LLMError):
    """Raised when the LLM backend is unreachable or disabled."""


class LLMProvider(ABC):
    """Interface every mentor LLM backend implements."""

    name: str = "base"

    @abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int) -> LLMResult:
        """Generate one completion from a system + user prompt pair."""

    @abstractmethod
    async def is_ready(self) -> bool:
        """Cheap readiness probe (model list / health endpoint)."""
