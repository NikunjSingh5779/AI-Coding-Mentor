"""Execution and problem-test orchestration."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.execution.sandbox import SandboxClient


class ExecutionService:
    def __init__(self, sandbox: SandboxClient) -> None:
        self.sandbox = sandbox

    async def run(
        self,
        code: str,
        language: str,
        stdin: str = "",
        timeout_seconds: int | None = None,
    ) -> dict:
        return await self.sandbox.execute(
            code,
            language,
            stdin=stdin,
            timeout_seconds=timeout_seconds,
        )

    async def run_problem_tests(
        self,
        code: str,
        problem: dict[str, Any],
        language: str,
    ) -> dict[str, Any]:
        """Execute function-style Python problems without invoking __main__ blocks."""

        entry_function = problem.get("entry_function")
        if language != "python":
            return {
                "passed": False,
                "tests": [],
                "error": "Problem tests currently target Python.",
            }
        if not entry_function:
            return {
                "passed": False,
                "tests": [],
                "error": "Problem has no entry_function",
            }

        results: list[dict[str, Any]] = []
        for case in problem.get("test_cases", []):
            payload = json.dumps(
                case.get("input", {}),
                separators=(",", ":"),
            )
            source = json.dumps(code)
            wrapper = (
                "import json\n"
                f"source = {source}\n"
                "namespace = {'__name__': 'solution'}\n"
                "exec(compile(source, 'solution.py', 'exec'), namespace)\n"
                f"payload = json.loads({payload!r})\n"
                f"result = namespace[{entry_function!r}](**payload)\n"
                "print(json.dumps({'result': result}))\n"
            )
            run = await self.sandbox.execute(
                wrapper,
                "python",
                timeout_seconds=15,
            )

            actual = None
            parse_error = None
            stdout = str(run.get("stdout", ""))
            if stdout.strip():
                try:
                    actual = json.loads(stdout.strip().splitlines()[-1])["result"]
                except Exception as exc:
                    parse_error = str(exc)

            expected = case.get("expected")
            passed = (
                bool(run.get("success"))
                and parse_error is None
                and actual == expected
            )
            results.append(
                {
                    "description": case.get("description", ""),
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                    "stdout": stdout,
                    "stderr": run.get("stderr", ""),
                    "error_type": run.get("error_type"),
                }
            )

        return {
            "passed": bool(results) and all(item["passed"] for item in results),
            "tests": results,
            "test_count": len(results),
            "passed_count": sum(1 for item in results if item["passed"]),
            "code_hash": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        }
