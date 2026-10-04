"""
Complete Python Code Analysis Pipeline for AI Real-Time Coding Screener
"""

import ast
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any


class DiagnosticSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CodeDiagnostic:
    line: int
    column: int
    message: str
    severity: DiagnosticSeverity
    source: str
    category: str


class PythonAnalyzer:
    """Complete Python code analysis with AST parsing, linting, and execution"""

    def __init__(self):
        self.diagnostics: list[CodeDiagnostic] = []

    def analyze(self, code: str) -> dict[str, Any]:
        """Run complete analysis pipeline on Python code"""
        self.diagnostics.clear()

        results = {
            "syntax_errors": self._check_syntax(code),
            "lint_issues": self._run_lint_checks(code),
            "execution_result": self._safe_execute(code),
            "code_quality": self._analyze_quality(code),
            "diagnostics": [
                {
                    "line": d.line,
                    "column": d.column,
                    "message": d.message,
                    "severity": d.severity.value,
                    "source": d.source,
                    "category": d.category,
                }
                for d in self.diagnostics
            ],
        }

        return results

    def _check_syntax(self, code: str) -> list[dict[str, Any]]:
        """Check Python syntax using AST parsing"""
        syntax_errors = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            error = {
                "line": e.lineno or 1,
                "column": e.offset or 1,
                "message": str(e.msg),
                "text": e.text or "",
            }
            syntax_errors.append(error)

            self.diagnostics.append(
                CodeDiagnostic(
                    line=e.lineno or 1,
                    column=e.offset or 1,
                    message=f"Syntax Error: {e.msg}",
                    severity=DiagnosticSeverity.ERROR,
                    source="ast_parser",
                    category="syntax",
                )
            )

        return syntax_errors

    def _run_lint_checks(self, code: str) -> list[dict[str, Any]]:
        """Run basic linting checks"""
        lint_issues = []

        try:
            tree = ast.parse(code)

            # Check for common issues
            for node in ast.walk(tree):
                # Unused imports (basic check)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Simple check - could be enhanced
                        if not self._is_name_used(tree, alias.name):
                            self.diagnostics.append(
                                CodeDiagnostic(
                                    line=node.lineno,
                                    column=node.col_offset,
                                    message=f"Unused import: {alias.name}",
                                    severity=DiagnosticSeverity.WARNING,
                                    source="linter",
                                    category="unused_import",
                                )
                            )

                # Function without docstring
                if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
                    if not node.name.startswith("_"):  # Skip private functions
                        self.diagnostics.append(
                            CodeDiagnostic(
                                line=node.lineno,
                                column=node.col_offset,
                                message=f"Function '{node.name}' missing docstring",
                                severity=DiagnosticSeverity.INFO,
                                source="linter",
                                category="documentation",
                            )
                        )

                # Bare except clause
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    self.diagnostics.append(
                        CodeDiagnostic(
                            line=node.lineno,
                            column=node.col_offset,
                            message="Bare except clause catches all exceptions",
                            severity=DiagnosticSeverity.WARNING,
                            source="linter",
                            category="exception_handling",
                        )
                    )

        except Exception:
            # If AST parsing failed, we already caught it in syntax check
            pass

        return lint_issues

    def _safe_execute(self, code: str) -> dict[str, Any]:
        """Safely execute code in a restricted environment"""
        execution_result = {
            "success": False,
            "output": "",
            "error": None,
            "execution_time": 0,
        }

        try:
            # Create a restricted execution environment
            restricted_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "abs": abs,
                    "max": max,
                    "min": min,
                    "sum": sum,
                    "sorted": sorted,
                    "reversed": reversed,
                    "enumerate": enumerate,
                    "zip": zip,
                }
            }

            # Capture output
            import contextlib
            import io

            output_buffer = io.StringIO()

            with contextlib.redirect_stdout(output_buffer):
                with contextlib.redirect_stderr(output_buffer):
                    exec(code, restricted_globals)

            execution_result["success"] = True
            execution_result["output"] = output_buffer.getvalue()

        except Exception as e:
            execution_result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
            }

            # Add runtime error to diagnostics
            self.diagnostics.append(
                CodeDiagnostic(
                    line=1,  # Could extract from traceback for better precision
                    column=1,
                    message=f"Runtime Error: {type(e).__name__}: {str(e)}",
                    severity=DiagnosticSeverity.ERROR,
                    source="executor",
                    category="runtime",
                )
            )

        return execution_result

    def _analyze_quality(self, code: str) -> dict[str, Any]:
        """Analyze code quality metrics"""
        quality_metrics = {
            "lines_of_code": len(code.splitlines()),
            "complexity": 1,  # Basic complexity
            "functions": 0,
            "classes": 0,
            "comments": 0,
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    quality_metrics["functions"] += 1
                elif isinstance(node, ast.ClassDef):
                    quality_metrics["classes"] += 1

            # Count comments (basic implementation)
            lines = code.splitlines()
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("#"):
                    quality_metrics["comments"] += 1

        except Exception:
            pass

        return quality_metrics

    def _is_name_used(self, tree: ast.AST, name: str) -> bool:
        """Check if a name is used in the AST (basic implementation)"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == name:
                return True
        return False


# Global analyzer instance
analyzer = PythonAnalyzer()
