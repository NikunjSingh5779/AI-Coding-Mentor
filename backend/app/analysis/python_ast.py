"""
Precise Python AST Syntax Analyzer.
Compiles code to find syntax/indentation errors safely without executing it.
"""

import ast
import uuid
import re
from typing import List, Optional
from app.schemas.diagnostic import Diagnostic, DiagnosticRange, Position, Severity, Origin
from app.analysis.taxonomy import Category
from app.analysis.aggregator import compute_fingerprint


def _categorize_syntax_error(msg: str) -> Category:
    msg_lower = msg.lower()
    if "indent" in msg_lower or "unindent" in msg_lower:
        return Category.SYNTAX_INDENTATION
    if "expected" in msg_lower or "was never closed" in msg_lower or "unmatched" in msg_lower:
        return Category.SYNTAX_MISSING_TOKEN
    return Category.SYNTAX_UNEXPECTED_TOKEN


def analyze_python_ast(code: str, seq: int = 0) -> List[Diagnostic]:
    """
    Run AST compilation on python code string.
    Returns syntax diagnostics if any syntax/indentation errors occur.
    """
    if not code:
        return []

    # Safeguard against extremely pathological inputs
    if len(code) > 200_000:
        return [
            Diagnostic(
                id=str(uuid.uuid4()),
                seq=seq,
                origin=Origin.PARSER,
                rule="E999",
                category=Category.SYNTAX_UNEXPECTED_TOKEN.value,
                severity=Severity.ERROR,
                message_raw="Source code exceeds maximum analyzable size limit.",
                range=DiagnosticRange(
                    start=Position(line=1, col=1),
                    end=Position(line=1, col=1)
                ),
                fingerprint=compute_fingerprint(
                    Category.SYNTAX_UNEXPECTED_TOKEN.value, "E999", None, ""
                ),
                confidence=1.0
            )
        ]

    diagnostics: List[Diagnostic] = []

    try:
        ast.parse(code)
    except SyntaxError as e:
        line = e.lineno or 1
        col = e.offset or 1
        end_line = getattr(e, "end_lineno", None) or line
        end_col = getattr(e, "end_offset", None) or (col + 1)
        msg = e.msg or "Syntax error"

        category = _categorize_syntax_error(msg)
        code_lines = code.splitlines()
        line_text = code_lines[line - 1] if 0 <= line - 1 < len(code_lines) else ""

        fp = compute_fingerprint(
            category=category.value,
            rule="E999",
            symbol_name=None,
            line_text=line_text
        )

        diagnostics.append(
            Diagnostic(
                id=str(uuid.uuid4()),
                seq=seq,
                origin=Origin.PARSER,
                rule="E999",
                category=category.value,
                severity=Severity.ERROR,
                message_raw=f"SyntaxError: {msg}",
                range=DiagnosticRange(
                    start=Position(line=line, col=col),
                    end=Position(line=end_line, col=end_col)
                ),
                fingerprint=fp,
                confidence=1.0
            )
        )
    except Exception as e:
        diagnostics.append(
            Diagnostic(
                id=str(uuid.uuid4()),
                seq=seq,
                origin=Origin.PARSER,
                rule="PARSER_FAIL",
                category=Category.SYNTAX_UNEXPECTED_TOKEN.value,
                severity=Severity.ERROR,
                message_raw=f"Parser error: {str(e)}",
                range=DiagnosticRange(
                    start=Position(line=1, col=1),
                    end=Position(line=1, col=1)
                ),
                fingerprint="parser_fail",
                confidence=0.5
            )
        )

    return diagnostics
