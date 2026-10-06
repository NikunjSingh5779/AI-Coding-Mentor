"""OpenAI-compatible chat-completions adapter (LM Studio, Ollama, vLLM, hosted APIs).

One adapter covers every provider exposing /chat/completions, per ADR Q4
(both local and hosted, switchable). Includes retry with backoff and a
readiness probe against the model list.
"""

from __future__ import annotations

import asyncio
import time

import httpx

from app.core.logging import get_logger

from .base import LLMError, LLMProvider, LLMResult, LLMUnavailable

logger = get_logger(__name__)

_RETRY_ATTEMPTS = 2
_RETRY_BACKOFF_S = 0.5


class OpenAICompatibleProvider(LLMProvider):
    """Adapter for any OpenAI-compatible /chat/completions endpoint."""

    name = "openai_compatible"

    def __init__(self, base_url: str, api_key: str, model: str, timeout_s: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(
            timeout=timeout_s,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def complete(self, system: str, user: str, max_tokens: int) -> LLMResult:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "stream": False,
        }
        last_error: Exception | None = None
        for attempt in range(_RETRY_ATTEMPTS + 1):
            t0 = time.perf_counter()
            try:
                resp = await self._client.post(f"{self._base_url}/chat/completions", json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"] or ""
                return LLMResult(
                    text=text,
                    model=self._model,
                    provider=self.name,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 1),
                    finish_reason=data["choices"][0].get("finish_reason", "stop"),
                )
            except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
                last_error = exc
                if attempt < _RETRY_ATTEMPTS:
                    await asyncio.sleep(_RETRY_BACKOFF_S * (2**attempt))
        raise LLMError(f"LLM call failed after {_RETRY_ATTEMPTS + 1} attempts: {last_error}")

    async def is_ready(self) -> bool:
        try:
            resp = await self._client.get(f"{self._base_url}/models")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def aclose(self) -> None:
        await self._client.aclose()


class DisabledProvider(LLMProvider):
    """Stub used when LLM_ENABLED=false; every call reports unavailable."""

    name = "disabled"

    async def complete(self, system: str, user: str, max_tokens: int) -> LLMResult:
        raise LLMUnavailable("LLM integration is disabled (LLM_ENABLED=false)")

    async def is_ready(self) -> bool:
        return False
