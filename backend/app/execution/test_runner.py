"""
Test runner service for evaluating learner code against problem test cases.
Ensures hidden test expected outputs and inputs are never exposed to the client per Q3.
"""

from typing import List, Optional
from app.execution.client import SandboxClient
from app.schemas.problem import Problem, TestCase
from app.schemas.run import RunResult, TestCaseResult, TestCaseSpec


class TestRunner:
    """Orchestrates test case execution against a problem definition."""

    def __init__(self, sandbox_client: Optional[SandboxClient] = None):
        self.client = sandbox_client or SandboxClient()

    async def run_problem_tests(
        self,
        problem: Problem,
        code: str,
        language: str = "python",
        include_hidden: bool = True,
    ) -> RunResult:
        """
        Run test cases for a given problem definition.
        Hidden test cases report pass/fail only; their input and expected output
        are redacted in the returned results.
        """
        tests_to_run: List[TestCase] = []
        for tc in problem.test_cases:
            if not tc.is_hidden or include_hidden:
                tests_to_run.append(tc)

        test_specs = [
            TestCaseSpec(
                id=tc.id,
                stdin=tc.stdin,
                expected_output=tc.expected_output,
                is_hidden=tc.is_hidden,
            )
            for tc in tests_to_run
        ]

        result = await self.client.run_tests(
            code=code,
            language=language,
            tests=test_specs,
            timeout_seconds=problem.timeout_seconds,
        )

        # Sanitize hidden test case outputs before returning
        if result.test_results:
            sanitized_results: List[TestCaseResult] = []
            for tr in result.test_results:
                if tr.is_hidden:
                    # Never reveal stdin or expected output of hidden tests
                    sanitized_results.append(
                        TestCaseResult(
                            id=tr.id,
                            passed=tr.passed,
                            stdout="[Hidden test case output hidden]" if not tr.passed else "",
                            stderr=tr.stderr if tr.exit_code != 0 else "",
                            exit_code=tr.exit_code,
                            duration_ms=tr.duration_ms,
                            is_hidden=True,
                            error_type=tr.error_type,
                        )
                    )
                else:
                    sanitized_results.append(tr)
            result.test_results = sanitized_results

        return result
