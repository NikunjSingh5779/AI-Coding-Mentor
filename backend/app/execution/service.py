"""Execution and problem-test orchestration."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.execution.sandbox import SandboxExecutor


class ExecutionService:
    def __init__(self, sandbox: SandboxExecutor) -> None:
        self.sandbox = sandbox

    async def run(
        self,
        code: str,
        language: str,
        stdin: str = "",
        timeout_seconds: int | None = None,
    ) -> dict:
        return await self.sandbox.execute(
            code, language, stdin=stdin, timeout_seconds=timeout_seconds
        )

    async def run_problem_tests(
        self,
        code: str,
        problem: dict[str, Any],
        language: str,
    ) -> dict[str, Any]:
        """Run problem cases through a generated JSON stdin protocol.

        The wrapper imports the learner source and invokes the configured entry
        function, so expected values are compared outside the learner process.
        """

        entry_function = problem.get("entry_function")
        if not entry_function:
            return {
                "passed": False,
                "tests": [],
                "error": "Problem has no entry_function",
            }

        tests = problem.get("test_cases", [])
        results = []

        for case in tests:
            payload = json.dumps(case["input"], separators=(",", ":"))
            wrapper = (
                f"import json\n"
                f"from main import {entry_function}\n"
                f"data=json.loads({payload!r})\n"
                f"result={entry_function}(**data)\n"
                f"print(json.dumps({{'result': result}}))\n"
            )
            run = await self.sandbox.execute(
                code + "\n" + wrapper,
                "python" if language == "python" else language,
                stdin="",
                timeout_seconds=15,
            )
            expected = case.get("expected")
            actual = None
            parse_error = None
            if run["stdout"].strip():
                try:
                    actual = json.loads(run["stdout"].strip().splitlines()[-1])["result"]
                except Exception as exc:
                    parse_error = str(exc)

            passed = (
                run["success"]
                and parse_error is None
                and actual == expected
            )
            results.append(
                {
                    "description": case.get("description", ""),
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                    "stdout": run["stdout"],
                    "stderr": run["stderr"],
                    "error_type": run.get("error_type"),
                }
            )

        return {
            "passed": bool(results) and all(item["passed"] for item in results),
            "tests": results,
            "test_count": len(results),
            "passed_count": sum(1 for item in results if item["passed"]),
            "code_hash": hashlib.sha256(code.encode()).hexdigest(),
        }
