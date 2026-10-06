"""Complexity and nesting metrics (P1 quality analyzer).

Pure AST analysis: cyclomatic complexity per function and max nesting depth.
Emits QUALITY_COMPLEXITY diagnostics for extreme cases only, to keep the
false-positive rate on clean code at zero.
"""

from __future__ import annotations

import ast

from app.schemas.diagnostic import Diagnostic, DiagnosticRange, Origin, Position, Severity

# Thresholds chosen to fire only on clearly complex beginner code.
MAX_COMPLEXITY = 15
MAX_NESTING = 5


def _fingerprint(name: str, line: int) -> str:
    import hashlib

    return hashlib.sha1(f"{name}:{line}".encode()).hexdigest()[:16]


def _branching_nodes(node: ast.AST) -> int:
    count = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.BoolOp, ast.ExceptHandler)):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
    return count


def _max_nesting(node: ast.AST, depth: int = 0) -> int:
    max_depth = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            max_depth = max(max_depth, _max_nesting(child, depth + 1))
        else:
            max_depth = max(max_depth, _max_nesting(child, depth))
    return max_depth


def analyze_complexity(code: str, seq: int = 0) -> list[Diagnostic]:
    """Return complexity diagnostics for a Python source string."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []  # syntax analyzer owns that failure mode

    diagnostics: list[Diagnostic] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1 + _branching_nodes(node)
            nesting = _max_nesting(node)
            line = node.lineno

            if complexity > MAX_COMPLEXITY:
                diagnostics.append(
                    Diagnostic(
                        id=f"cx-{_fingerprint(node.name, line)}",
                        seq=seq,
                        origin=Origin.LINTER,
                        rule="complexity",
                        category="QUALITY_COMPLEXITY",
                        severity=Severity.INFO,
                        message_raw=f"Function '{node.name}' has complexity {complexity} (>{MAX_COMPLEXITY})",
                        range=DiagnosticRange(
                            start=Position(line=line, col=1),
                            end=Position(line=line, col=20),
                        ),
                        fingerprint=_fingerprint(f"cx-{node.name}", line),
                    )
                )
            if nesting >= MAX_NESTING:
                diagnostics.append(
                    Diagnostic(
                        id=f"nest-{_fingerprint(node.name, line)}",
                        seq=seq,
                        origin=Origin.LINTER,
                        rule="nesting",
                        category="QUALITY_COMPLEXITY",
                        severity=Severity.INFO,
                        message_raw=f"Function '{node.name}' nests {nesting} levels deep (>= {MAX_NESTING})",
                        range=DiagnosticRange(
                            start=Position(line=line, col=1),
                            end=Position(line=line, col=20),
                        ),
                        fingerprint=_fingerprint(f"nest-{node.name}", line),
                    )
                )
    return diagnostics
