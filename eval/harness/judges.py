"""Automatic hint checks (deterministic judges) for the hints eval.

Checks hint outputs for: guardrail compliance (no code fences at H1-H3,
no solution phrasing), non-emptiness, length bounds and beginner-friendly
language. Optional LLM-judge scoring is out of scope for the local eval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_FENCED_CODE = re.compile(r"```|~~~")
_SOLUTION_MARKERS = re.compile(
    r"(?i)\b(here is the (complete|full|fixed) (solution|code)|copy this|just replace (your|the) (function|code) with)"
)
_JARGON = re.compile(r"\b(monomorphization|reification|homiconicity|variance annotation)\b", re.IGNORECASE)


@dataclass
class HintJudgement:
    """Result of judging one generated hint."""

    passed: bool
    checks: dict[str, bool]
    failures: list[str]


def judge_hint(text: str, level: int) -> HintJudgement:
    """Run deterministic checks against one hint."""
    checks: dict[str, bool] = {}
    failures: list[str] = []

    checks["non_empty"] = bool(text and text.strip())
    if not checks["non_empty"]:
        failures.append("empty")

    checks["length_ok"] = 0 < len(text) <= 800
    if not checks["length_ok"]:
        failures.append("length")

    checks["no_fenced_code"] = not bool(_FENCED_CODE.search(text)) if level <= 3 else True
    if not checks["no_fenced_code"]:
        failures.append("fenced_code_at_H1-H3")

    checks["no_solution_leak"] = not bool(_SOLUTION_MARKERS.search(text)) if level <= 3 else True
    if not checks["no_solution_leak"]:
        failures.append("solution_leak")

    checks["no_heavy_jargon"] = not bool(_JARGON.search(text))
    if not checks["no_heavy_jargon"]:
        failures.append("jargon")

    passed = all(checks.values())
    return HintJudgement(passed=passed, checks=checks, failures=failures)
