"""Lightweight syntax/quality analysis for non-Python languages.

The fast path deliberately avoids executing learner code. It catches structural
syntax errors cheaply; definitive compile/test feedback comes from the sandbox.
"""

from __future__ import annotations

import re
import uuid

from app.schemas.diagnostic import Diagnostic, DiagnosticRange, Origin, Position, Severity


def _diag(language: str, line: int, message: str, rule: str) -> Diagnostic:
    category = "SYNTAX_UNEXPECTED_TOKEN"
    if rule == "STYLE_VAR":
        category = "QUALITY_STYLE"
    return Diagnostic(
        id=str(uuid.uuid4()),
        seq=0,
        origin=Origin.PARSER,
        rule=rule,
        category=category,
        severity=Severity.ERROR if category.startswith("SYNTAX") else Severity.INFO,
        message_raw=message,
        range=DiagnosticRange(
            start=Position(line=max(1, line), col=1),
            end=Position(line=max(1, line), col=2),
        ),
        fingerprint=f"{language}:{rule}:{line}",
        confidence=0.65,
    )


def analyze_polyglot(code: str, language: str, seq: int = 0) -> list[Diagnostic]:
    language = language.lower()
    diagnostics: list[Diagnostic] = []
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    opening = set(pairs.values())

    for line_no, line in enumerate(code.splitlines(), 1):
        for char in line:
            if char in opening:
                stack.append((char, line_no))
            elif char in pairs:
                if not stack or stack[-1][0] != pairs[char]:
                    diagnostics.append(
                        _diag(
                            language,
                            line_no,
                            f"Unmatched closing delimiter {char}.",
                            "UNMATCHED_DELIMITER",
                        )
                    )
                else:
                    stack.pop()

        if language in {"javascript", "typescript"} and re.search(r"\bvar\s+", line):
            diagnostics.append(
                _diag(
                    language,
                    line_no,
                    "Prefer let/const for block-scoped declarations.",
                    "STYLE_VAR",
                )
            )

    for char, line_no in stack[-3:]:
        diagnostics.append(
            _diag(
                language,
                line_no,
                f"Unclosed delimiter {char}.",
                "UNCLOSED_DELIMITER",
            )
        )

    for diagnostic in diagnostics:
        diagnostic.seq = seq
    return diagnostics
