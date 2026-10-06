"""HTTP client for the dedicated sandbox runner."""

from __future__ import annotations

import httpx


class SandboxUnavailable(RuntimeError):
    """The sandbox service cannot be reached or is not ready."""


class SandboxClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 65.0,
        max_code_bytes: int = 250_000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_code_bytes = max_code_bytes

    async def execute(
        self,
        code: str,
        language: str,
        stdin: str = "",
        timeout_seconds: int | None = None,
    ) -> dict:
        if len(code.encode("utf-8")) > self.max_code_bytes:
            raise ValueError("Code exceeds maximum size")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/execute",
                    headers={"X-Sandbox-Secret": self.secret},
                    json={
                        "code": code,
                        "language": language,
                        "stdin": stdin,
                        "timeout": timeout_seconds or 30,
                    },
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            raise SandboxUnavailable(
                f"Sandbox service unavailable: {exc}"
            ) from exc
