"""
Extract ERROR and MISSING nodes from Tree-sitter AST as syntax diagnostics.
"""

import uuid
from typing import List, Optional
from app.schemas.diagnostic import Diagnostic, DiagnosticRange, Position, Severity, Origin
from app.analysis.taxonomy import Category
from app.analysis.aggregator import compute_fingerprint
from app.analysis.treesitter.parser import parse_code


def _find_syntax_error_nodes(node, results: List):
    """Recursively find ERROR, MISSING, or nodes containing errors in Tree-sitter tree."""
    if node.is_missing:
        results.append((node, "MISSING"))
    elif node.type == "ERROR":
        results.append((node, "ERROR"))
    elif node.has_error:
        for child in node.children:
            _find_syntax_error_nodes(child, results)


def extract_treesitter_diagnostics(
    code: str,
    language: str = "python",
    seq: int = 0
) -> List[Diagnostic]:
    """
    Parse code using Tree-sitter and extract syntax diagnostics for ERROR and MISSING nodes.
    """
    if not code:
        return []

    tree = parse_code(code, language)
    if not tree or not tree.root_node.has_error:
        return []

    error_nodes = []
    _find_syntax_error_nodes(tree.root_node, error_nodes)

    diagnostics: List[Diagnostic] = []
    code_lines = code.splitlines()

    for node, err_type in error_nodes:
        # Tree-sitter positions are 0-indexed (row, column)
        start_row, start_col = node.start_point
        end_row, end_col = node.end_point

        # Convert to 1-indexed line, 1-indexed col
        line = start_row + 1
        col = start_col + 1
        end_line = end_row + 1
        end_col = max(col + 1, end_col + 1)

        if err_type == "MISSING":
            category = Category.SYNTAX_MISSING_TOKEN
            msg = f"Syntax error: Missing expected token '{node.type}'"
        else:
            category = Category.SYNTAX_UNEXPECTED_TOKEN
            msg = "Syntax error: Unexpected token or invalid construct"

        line_text = code_lines[line - 1] if 0 <= line - 1 < len(code_lines) else ""
        fp = compute_fingerprint(
            category=category.value,
            rule=err_type,
            symbol_name=None,
            line_text=line_text
        )

        diagnostics.append(
            Diagnostic(
                id=str(uuid.uuid4()),
                seq=seq,
                origin=Origin.TREESITTER,
                rule=err_type,
                category=category.value,
                severity=Severity.ERROR,
                message_raw=msg,
                range=DiagnosticRange(
                    start=Position(line=line, col=col),
                    end=Position(line=end_line, col=end_col)
                ),
                fingerprint=fp,
                confidence=0.9
            )
        )

    return diagnostics
