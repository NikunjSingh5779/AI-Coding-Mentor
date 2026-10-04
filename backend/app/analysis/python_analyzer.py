"""
Enhanced Python Code Analysis Pipeline for AI Real-Time Coding Screener
Provides comprehensive syntax, semantic, and quality analysis with error recovery.
"""

import ast
import re
import time
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, List, Dict, Set
import keyword
import builtins


class DiagnosticSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class CodeDiagnostic:
    line: int
    column: int
    end_line: Optional[int]
    end_column: Optional[int]
    message: str
    severity: DiagnosticSeverity
    source: str
    category: str
    code: Optional[str] = None
    fix_suggestion: Optional[str] = None


class AnalysisContext:
    """Context for tracking analysis state and performance metrics"""

    def __init__(self):
        self.start_time = time.time()
        self.lines_of_code = 0
        self.has_syntax_errors = False
        self.analysis_time_ms = 0
        self.defined_names: Set[str] = set()
        self.used_names: Set[str] = set()
        self.imported_names: Set[str] = set()
        self.function_names: Set[str] = set()
        self.class_names: Set[str] = set()


class PythonAnalyzer:
    """
    Enhanced Python code analyzer with comprehensive static analysis.

    Features:
    - Syntax analysis with error recovery
    - Semantic analysis (undefined variables, unused imports)
    - Style linting (PEP 8, naming conventions)
    - Quality metrics (complexity, maintainability)
    - Performance optimization for real-time analysis
    """
    def __init__(self):
        self.diagnostics: List[CodeDiagnostic] = []
        self.context = AnalysisContext()

    def analyze(self, code: str, max_time_ms: int = 100) -> Dict[str, Any]:
        """
        Run comprehensive analysis pipeline on Python code.

        Args:
            code: Python source code to analyze
            max_time_ms: Maximum analysis time in milliseconds

        Returns:
            Dictionary containing analysis results and diagnostics
        """
        self.context = AnalysisContext()
        self.context.start_time = time.time()
        self.diagnostics.clear()

        # Early validation
        if not code or not code.strip():
            return self._empty_result()

        self.context.lines_of_code = len(code.splitlines())

        # Run analysis pipeline with time budget
        try:
            # Phase 1: Syntax analysis (most critical)
            syntax_errors = self._check_syntax(code)

            # Phase 2: Semantic analysis (if syntax is valid)
            if not self.context.has_syntax_errors and self._time_remaining_ms() > 20:
                self._analyze_semantics(code)

            # Phase 3: Style and quality (if time permits)
            if self._time_remaining_ms() > 10:
                self._analyze_style(code)
                self._analyze_quality(code)

        except Exception as e:
            # Graceful degradation - return partial results
            self._add_diagnostic(
                1, 0, f"Analysis error: {str(e)}",
                DiagnosticSeverity.WARNING, "analyzer", "internal"
            )

        # Calculate final metrics
        self.context.analysis_time_ms = int((time.time() - self.context.start_time) * 1000)

        return {
            "diagnostics": [self._diagnostic_to_dict(d) for d in self.diagnostics],
            "analysis_time_ms": self.context.analysis_time_ms,
            "lines_of_code": self.context.lines_of_code,
            "has_syntax_errors": self.context.has_syntax_errors,
            "performance": {
                "within_budget": self.context.analysis_time_ms <= max_time_ms,
                "diagnostic_count": len(self.diagnostics)
            }
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty analysis result for invalid input"""
        return {
            "diagnostics": [],
            "analysis_time_ms": 0,
            "lines_of_code": 0,
            "has_syntax_errors": False,
            "performance": {"within_budget": True, "diagnostic_count": 0}
        }

    def _time_remaining_ms(self) -> int:
        """Calculate remaining analysis time in milliseconds"""
        elapsed_ms = int((time.time() - self.context.start_time) * 1000)
        return max(0, 100 - elapsed_ms)  # 100ms budget


    def _check_syntax(self, code: str) -> None:
        """
        Check Python syntax using AST parsing with error recovery.

        Args:
            code: Python source code to analyze
        """
        try:
            tree = ast.parse(code)
            # Collect defined and used names for semantic analysis
            self._collect_names(tree)

        except SyntaxError as e:
            self.context.has_syntax_errors = True
            self._add_diagnostic(
                line=e.lineno or 1,
                column=e.offset or 0,
                message=f"Syntax Error: {e.msg}",
                severity=DiagnosticSeverity.ERROR,
                source="ast_parser",
                category="syntax",
                code="E999",
                fix_suggestion=self._suggest_syntax_fix(e)
            )

        except Exception as e:
            # Fallback for other parsing errors
            self._add_diagnostic(
                1, 0, f"Parse error: {str(e)}",
                DiagnosticSeverity.ERROR, "ast_parser", "parse"
            )

    def _analyze_semantics(self, code: str) -> None:
        """
        Perform semantic analysis including undefined variables and unused imports.

        Args:
            code: Python source code to analyze
        """
        try:
            tree = ast.parse(code)

            # Check for undefined variables
            self._check_undefined_variables(tree)

            # Check for unused imports
            self._check_unused_imports(tree, code)

            # Check for duplicate definitions
            self._check_duplicate_definitions(tree)

        except Exception:
            # Skip semantic analysis if AST parsing fails
            pass

    def _analyze_style(self, code: str) -> None:
        """
        Analyze code style including PEP 8 violations and naming conventions.

        Args:
            code: Python source code to analyze
        """
        try:
            tree = ast.parse(code)
            lines = code.splitlines()

            # Check line length (PEP 8: 79 characters)
            for i, line in enumerate(lines, 1):
                if len(line) > 79:
                    self._add_diagnostic(
                        i, 79, f"Line too long ({len(line)} > 79 characters)",
                        DiagnosticSeverity.WARNING, "style", "line_length",
                        code="E501"
                    )

            # Check naming conventions
            self._check_naming_conventions(tree)

            # Check for missing docstrings
            self._check_missing_docstrings(tree)

            # Check for bare except clauses
            self._check_bare_except(tree)

        except Exception:
            # Skip style analysis if parsing fails
            pass

    def _analyze_quality(self, code: str) -> None:
        """
        Analyze code quality metrics including complexity and maintainability.

        Args:
            code: Python source code to analyze
        """
        try:
            tree = ast.parse(code)

            # Calculate cyclomatic complexity
            complexity = self._calculate_complexity(tree)
            if complexity > 10:
                self._add_diagnostic(
                    1, 0, f"High cyclomatic complexity: {complexity}",
                    DiagnosticSeverity.INFO, "quality", "complexity",
                    fix_suggestion="Consider breaking this function into smaller functions"
                )

            # Check for code smells
            self._check_code_smells(tree)

        except Exception:
            # Skip quality analysis if parsing fails
            pass

    def _collect_names(self, tree: ast.AST) -> None:
        """Collect all defined and used names in the AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.context.function_names.add(node.name)
                self.context.defined_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                self.context.class_names.add(node.name)
                self.context.defined_names.add(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name
                    self.context.imported_names.add(name)
                    self.context.defined_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    self.context.imported_names.add(name)
                    self.context.defined_names.add(name)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    self.context.defined_names.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    self.context.used_names.add(node.id)

    def _check_undefined_variables(self, tree: ast.AST) -> None:
        """Check for potentially undefined variables"""
        built_in_names = set(dir(builtins))

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                name = node.id
                # Check if name is defined, imported, or built-in
                if (name not in self.context.defined_names and
                    name not in self.context.imported_names and
                    name not in built_in_names and
                    name not in keyword.kwlist):

                    self._add_diagnostic(
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Undefined name '{name}'",
                        severity=DiagnosticSeverity.ERROR,
                        source="semantic",
                        category="undefined_name",
                        code="F821",
                        fix_suggestion=f"Define '{name}' before using it or check spelling"
                    )

    def _check_unused_imports(self, tree: ast.AST, code: str) -> None:
        """Check for unused import statements"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    name = alias.asname or alias.name
                    # Simple check: is the imported name used anywhere in the code?
                    if name not in self.context.used_names:
                        self._add_diagnostic(
                            line=node.lineno,
                            column=node.col_offset,
                            message=f"Unused import '{name}'",
                            severity=DiagnosticSeverity.WARNING,
                            source="linter",
                            category="unused_import",
                            code="F401",
                            fix_suggestion=f"Remove unused import '{name}'"
                        )

    def _check_duplicate_definitions(self, tree: ast.AST) -> None:
        """Check for duplicate function or class definitions"""
        functions_seen = set()
        classes_seen = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in functions_seen:
                    self._add_diagnostic(
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Redefinition of function '{node.name}'",
                        severity=DiagnosticSeverity.WARNING,
                        source="linter",
                        category="redefinition",
                        code="F811"
                    )
                functions_seen.add(node.name)
            elif isinstance(node, ast.ClassDef):
                if node.name in classes_seen:
                    self._add_diagnostic(
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Redefinition of class '{node.name}'",
                        severity=DiagnosticSeverity.WARNING,
                        source="linter",
                        category="redefinition",
                        code="F811"
                    )
                classes_seen.add(node.name)

    def _check_naming_conventions(self, tree: ast.AST) -> None:
        """Check PEP 8 naming conventions"""
        for node in ast.walk(tree):
            # Function names should be snake_case
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and not node.name.startswith('__'):
                    self._add_diagnostic(
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Function name '{node.name}' should use snake_case",
                        severity=DiagnosticSeverity.INFO,
                        source="style",
                        category="naming",
                        code="N802",
                        fix_suggestion=f"Rename to '{self._to_snake_case(node.name)}'"
                    )

            # Class names should be PascalCase
            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    self._add_diagnostic(
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Class name '{node.name}' should use PascalCase",
                        severity=DiagnosticSeverity.INFO,
                        source="style",
                        category="naming",
                        code="N801",
                        fix_suggestion=f"Rename to '{self._to_pascal_case(node.name)}'"
                    )

    def _check_missing_docstrings(self, tree: ast.AST) -> None:
        """Check for missing docstrings in public functions and classes"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # Skip private members (starting with _)
                if not node.name.startswith('_') and not ast.get_docstring(node):
                    entity_type = "Function" if isinstance(node, ast.FunctionDef) else "Class"
                    self._add_diagnostic(
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"{entity_type} '{node.name}' missing docstring",
                        severity=DiagnosticSeverity.INFO,
                        source="style",
                        category="documentation",
                        code="D100" if isinstance(node, ast.FunctionDef) else "D101",
                        fix_suggestion="Add a docstring explaining what this does"
                    )

    def _check_bare_except(self, tree: ast.AST) -> None:
        """Check for bare except clauses"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                self._add_diagnostic(
                    line=node.lineno,
                    column=node.col_offset,
                    message="Bare except clause catches all exceptions (including SystemExit)",
                    severity=DiagnosticSeverity.WARNING,
                    source="linter",
                    category="exception_handling",
                    code="E722",
                    fix_suggestion="Specify exception type like 'except Exception:'"
                )

    def _check_code_smells(self, tree: ast.AST) -> None:
        """Check for common code smells"""
        for node in ast.walk(tree):
            # Deeply nested code (more than 3 levels)
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth = self._get_nesting_depth(node)
                if depth > 3:
                    self._add_diagnostic(
                        line=node.lineno,
                        column=node.col_offset,
                        message=f"Deeply nested code (depth: {depth})",
                        severity=DiagnosticSeverity.INFO,
                        source="quality",
                        category="nesting",
                        fix_suggestion="Consider refactoring to reduce nesting"
                    )

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate basic cyclomatic complexity"""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            # Decision points increase complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # and/or operators add complexity
                complexity += len(node.values) - 1

        return complexity

    def _get_nesting_depth(self, node: ast.AST) -> int:
        """Calculate nesting depth of a node"""
        depth = 0
        parent = getattr(node, 'parent', None)
        while parent:
            if isinstance(parent, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth += 1
            parent = getattr(parent, 'parent', None)
        return depth

    def _suggest_syntax_fix(self, error: SyntaxError) -> Optional[str]:
        """Suggest fixes for common syntax errors"""
        msg = str(error.msg).lower()
        if "invalid syntax" in msg:
            return "Check for missing colons, mismatched parentheses, or typo in keywords"
        elif "unexpected eof" in msg:
            return "Missing closing bracket, parenthesis, or quote"
        elif "indentation" in msg:
            return "Check indentation - Python requires consistent spaces or tabs"
        elif "never closed" in msg:
            return "Closing delimiter missing"
        return None

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase"""
        return ''.join(word.capitalize() for word in name.split('_'))

    def _add_diagnostic(
        self, line: int, column: int, message: str,
        severity: DiagnosticSeverity, source: str, category: str,
        code: Optional[str] = None, fix_suggestion: Optional[str] = None,
        end_line: Optional[int] = None, end_column: Optional[int] = None
    ) -> None:
        """Add a diagnostic to the collection"""
        self.diagnostics.append(
            CodeDiagnostic(
                line=line,
                column=column,
                end_line=end_line,
                end_column=end_column,
                message=message,
                severity=severity,
                source=source,
                category=category,
                code=code,
                fix_suggestion=fix_suggestion
            )
        )

    def _diagnostic_to_dict(self, diagnostic: CodeDiagnostic) -> Dict[str, Any]:
        """Convert a diagnostic to dictionary format for API responses"""
        return {
            "line": diagnostic.line,
            "column": diagnostic.column,
            "end_line": diagnostic.end_line,
            "end_column": diagnostic.end_column,
            "message": diagnostic.message,
            "severity": diagnostic.severity.value,
            "source": diagnostic.source,
            "category": diagnostic.category,
            "code": diagnostic.code,
            "fix_suggestion": diagnostic.fix_suggestion
        }


# Global analyzer instance
analyzer = PythonAnalyzer()


# CLI test interface for development
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test cases for development
        test_cases = [
            # Syntax error
            "def hello(\n    print('missing closing paren')",

            # Undefined variable
            "print(undefined_variable)",

            # Unused import
            "import os\nprint('hello')",

            # Style issues
            "def badFunctionName():\n    pass",

            # Valid code
            "def hello_world():\n    \"\"\"Say hello to the world.\"\"\"\n    print('Hello, world!')\n    return True",
        ]

        print("Testing Python Analyzer...")
        for i, code in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i} ---")
            print(f"Code: {repr(code[:50])}...")

            result = analyzer.analyze(code)
            print(f"Analysis time: {result['analysis_time_ms']}ms")
            print(f"Diagnostics: {len(result['diagnostics'])}")

            for diag in result['diagnostics']:
                severity_icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️", "hint": "💡"}
                icon = severity_icon.get(diag['severity'], "•")
                print(f"  {icon} Line {diag['line']}: {diag['message']}")

        print("\n✅ All test cases completed!")
    else:
        print("Python Code Analyzer")
        print("Usage: python -m app.analysis.python_analyzer --test")
