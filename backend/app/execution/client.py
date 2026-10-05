"""
Sandbox Runner HTTP Client with Circuit Breaker and Execution Safeguards.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings
from app.execution.result_parser import parse_execution_result_to_diagnostics
from app.schemas.run import RunResult, TestCaseResult, TestCaseSpec

logger = logging.getLogger("app.execution.client")


class CircuitState(str, Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject early
    HALF_OPEN = "half_open"  # Probing for recovery


class CircuitBreaker:
    """Circuit breaker pattern to protect against runner outages."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 15.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def record_success(self):
        """Record a successful response."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        """Record a failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning("Sandbox circuit breaker OPENED due to repeated runner failures")

    def can_attempt(self) -> bool:
        """Check whether a request is allowed through."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout_sec:
                self.state = CircuitState.HALF_OPEN
                logger.info("Sandbox circuit breaker transitioning to HALF_OPEN probe")
                return True
            return False

        # HALF_OPEN: allow a single probe
        return True


class SandboxClient:
    """Client for executing code against the isolated sandbox runner service."""

    def __init__(self):
        self.settings = get_settings()
        self.circuit_breaker = CircuitBreaker()

    @property
    def is_enabled(self) -> bool:
        return self.settings.execution_enabled

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "X-Sandbox-Secret": self.settings.sandbox_secret,
            "Content-Type": "application/json",
        }

    async def health_check(self) -> bool:
        """Check if the sandbox runner service is online and healthy."""
        if not self.is_enabled:
            return False

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(
                    f"{self.settings.sandbox_url}/health",
                    headers=self.headers,
                )
                return res.status_code == 200
        except Exception:
            return False

    async def run_code(
        self,
        code: str,
        language: str = "python",
        stdin: str = "",
        timeout_seconds: float = 5.0,
    ) -> RunResult:
        """Execute a single code snippet in the sandbox."""
        if not self.is_enabled:
            return RunResult(
                status="disabled",
                exit_code=-1,
                stdout="",
                stderr="Code execution is disabled by configuration (EXECUTION_ENABLED=false).",
                duration_ms=0.0,
            )

        if not self.circuit_breaker.can_attempt():
            return RunResult(
                status="busy",
                exit_code=-1,
                stdout="",
                stderr="Sandbox runner is currently unavailable (circuit breaker open).",
                duration_ms=0.0,
            )

        payload = {
            "language": language,
            "files": {
                "main.py": code,
            },
            "stdin": stdin,
            "mode": "run",
            "limits": {
                "timeout_seconds": timeout_seconds,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds + 3.0) as client:
                response = await client.post(
                    f"{self.settings.sandbox_url}/jobs",
                    json=payload,
                    headers=self.headers,
                )

                if response.status_code == 429 or (response.status_code == 200 and response.json().get("status") == "busy"):
                    return RunResult(
                        status="busy",
                        exit_code=-1,
                        stdout="",
                        stderr="Runner busy: concurrency limit reached. Please try again shortly.",
                        duration_ms=0.0,
                    )

                if response.status_code != 200:
                    self.circuit_breaker.record_failure()
                    return RunResult(
                        status="error",
                        exit_code=-1,
                        stdout="",
                        stderr=f"Sandbox runner HTTP {response.status_code}: {response.text}",
                        duration_ms=0.0,
                    )

                data = response.json()
                self.circuit_breaker.record_success()

                diagnostics = parse_execution_result_to_diagnostics(
                    status=data.get("status", "error"),
                    exit_code=data.get("exit_code", 0),
                    stdout=data.get("stdout", ""),
                    stderr=data.get("stderr", ""),
                    code=code,
                )

                return RunResult(
                    status=data.get("status", "success"),
                    exit_code=data.get("exit_code", 0),
                    stdout=data.get("stdout", ""),
                    stderr=data.get("stderr", ""),
                    duration_ms=data.get("duration_ms", 0.0),
                    truncated=data.get("truncated", False),
                    diagnostics=diagnostics,
                )

        except httpx.TimeoutException:
            self.circuit_breaker.record_failure()
            return RunResult(
                status="timeout",
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox request timed out after {timeout_seconds} seconds.",
                duration_ms=timeout_seconds * 1000.0,
            )
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.exception("Failed to communicate with sandbox runner")
            return RunResult(
                status="error",
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox connection error: {str(e)}",
                duration_ms=0.0,
            )

    async def run_tests(
        self,
        code: str,
        language: str,
        tests: List[TestCaseSpec],
        timeout_seconds: float = 5.0,
    ) -> RunResult:
        """Execute code against problem test cases."""
        if not self.is_enabled:
            return RunResult(
                status="disabled",
                exit_code=-1,
                stdout="",
                stderr="Code execution is disabled by configuration.",
                duration_ms=0.0,
            )

        if not self.circuit_breaker.can_attempt():
            return RunResult(
                status="busy",
                exit_code=-1,
                stdout="",
                stderr="Sandbox runner is currently unavailable (circuit breaker open).",
                duration_ms=0.0,
            )

        payload = {
            "language": language,
            "files": {
                "main.py": code,
            },
            "mode": "test",
            "tests": [test.model_dump() for test in tests],
            "limits": {
                "timeout_seconds": timeout_seconds,
            },
        }

        try:
            total_timeout = (timeout_seconds * len(tests)) + 5.0
            async with httpx.AsyncClient(timeout=total_timeout) as client:
                response = await client.post(
                    f"{self.settings.sandbox_url}/jobs",
                    json=payload,
                    headers=self.headers,
                )

                if response.status_code != 200:
                    self.circuit_breaker.record_failure()
                    return RunResult(
                        status="error",
                        exit_code=-1,
                        stdout="",
                        stderr=f"Sandbox runner HTTP {response.status_code}: {response.text}",
                        duration_ms=0.0,
                    )

                data = response.json()
                self.circuit_breaker.record_success()

                raw_test_results = data.get("test_results") or []
                test_results = [TestCaseResult(**tr) for tr in raw_test_results]
                all_passed = all(tr.passed for tr in test_results) if test_results else False

                diagnostics = parse_execution_result_to_diagnostics(
                    status=data.get("status", "error"),
                    exit_code=data.get("exit_code", 0),
                    stdout=data.get("stdout", ""),
                    stderr=data.get("stderr", ""),
                    code=code,
                )

                return RunResult(
                    status="success" if all_passed else data.get("status", "error"),
                    exit_code=data.get("exit_code", 0),
                    stdout=data.get("stdout", ""),
                    stderr=data.get("stderr", ""),
                    duration_ms=data.get("duration_ms", 0.0),
                    truncated=data.get("truncated", False),
                    diagnostics=diagnostics,
                    test_results=test_results,
                    all_passed=all_passed,
                )

        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.exception("Failed to run problem tests in sandbox")
            return RunResult(
                status="error",
                exit_code=-1,
                stdout="",
                stderr=f"Sandbox connection error: {str(e)}",
                duration_ms=0.0,
            )
