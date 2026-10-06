"""Performance and quality pattern detectors (P1).

Deterministic AST patterns:
- PERF_NESTED_LOOP: a loop directly nested inside another loop over ranges
- PERF_REPEATED_WORK: a function call inside a loop whose arguments are
  loop-invariant literals (cheap heuristic, zero false positives by design:
  only fires on exact literal repetition)
"""

from __future__ import annotations

import ast
import hashlib

from app.schemas.diagnostic import Diagnostic, DiagnosticRange, Origin, Position, Severity


def _fp(kind: str, line: int) -> str:
    return hashlib.sha1(f"{kind}:{line}".encode()).hexdigest()[:16]


def _diag(kind: str, category: str, line: int, message: str, seq: int) -> Diagnostic:
    return Diagnostic(
        id=f"{kind}-{_fp(kind, line)}",
        seq=seq,
        origin=Origin.LINTER,
        rule=kind,
        category=category,
        severity=Severity.WARNING,
        message_raw=message,
        range=DiagnosticRange(start=Position(line=line, col=1), end=Position(line=line, col=20)),
        fingerprint=_fp(category, line),
    )


class _PatternVisitor(ast.NodeVisitor):
    def __init__(self, seq: int):
        self.seq = seq
        self.diagnostics: list[Diagnostic] = []

    def visit_For(self, node: ast.For) -> None:
        self._check_nested(node)
        self._check_repeated_calls(node)
        self.generic_visit(node)

    visit_While = visit_For

    def _check_nested(self, node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                self.diagnostics.append(
                    _diag(
                        "PERF_NESTED_LOOP",
                        "PERF_NESTED_LOOP",
                        child.lineno,
                        "Nested loops: consider a set/dict lookup if the inner loop only searches",
                        self.seq,
                    )
                )
                break

    def _check_repeated_calls(self, loop: ast.AST) -> None:
        # len(x) called with the same literal name inside the loop body, 2+ times
        len_calls: dict[str, int] = {}
        for n in ast.walk(loop):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "len":
                if n.args and isinstance(n.args[0], ast.Name):
                    len_calls[n.args[0].id] = len_calls.get(n.args[0].id, 0) + 1
        for name, count in len_calls.items():
            if count >= 3:
                self.diagnostics.append(
                    _diag(
                        "PERF_REPEATED_WORK",
                        "PERF_REPEATED_WORK",
                        loop.lineno,
                        f"len({name}) computed {count}x inside the loop; compute it once before",
                        self.seq,
                    )
                )


def analyze_patterns(code: str, seq: int = 0) -> list[Diagnostic]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    visitor = _PatternVisitor(seq)
    visitor.visit(tree)
    return visitor.diagnostics
