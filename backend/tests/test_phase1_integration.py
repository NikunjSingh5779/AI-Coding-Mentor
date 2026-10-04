"""
Phase 1 Integration Test Suite
Tests the complete real-time code analysis pipeline end-to-end.
"""

import time
import asyncio
import json
from typing import Dict, Any

from app.analysis.python_analyzer import analyzer
from app.ws.endpoint import manager, WebSocketSession


def test_analyzer_syntax_error():
    """Test analyzer detects syntax errors correctly."""
    code = "def invalid_syntax(\n    print('missing paren')"
    result = analyzer.analyze(code)

    assert result["has_syntax_errors"] is True
    assert len(result["diagnostics"]) > 0
    assert result["diagnostics"][0]["severity"] == "error"
    assert "Syntax Error" in result["diagnostics"][0]["message"]
    print("[OK] Syntax error detection passed")


def test_analyzer_undefined_variable():
    """Test analyzer detects undefined variables."""
    code = "def test_func():\n    return undefined_var"
    result = analyzer.analyze(code)

    # Should detect undefined variable
    undefined_diags = [d for d in result["diagnostics"] if d["category"] == "undefined_name"]
    assert len(undefined_diags) > 0
    assert "undefined_var" in undefined_diags[0]["message"]
    print("[OK] Undefined variable detection passed")


def test_analyzer_unused_import():
    """Test analyzer detects unused imports."""
    code = "import os\nimport sys\n\nprint('hello')"
    result = analyzer.analyze(code)

    # Should detect unused imports
    unused_diags = [d for d in result["diagnostics"] if d["category"] == "unused_import"]
    assert len(unused_diags) >= 1
    print("[OK] Unused import detection passed")


def test_analyzer_pep8_naming():
    """Test analyzer detects PEP 8 naming violations."""
    code = "def badFunctionName():\n    pass\n\nclass bad_class_name:\n    pass"
    result = analyzer.analyze(code)

    # Should detect naming issues
    naming_diags = [d for d in result["diagnostics"] if d["category"] == "naming"]
    assert len(naming_diags) >= 2
    print("[OK] PEP 8 naming convention checks passed")


def test_analyzer_performance():
    """Test analyzer meets performance targets (<100ms)."""
    # Create medium-sized Python code (100 lines)
    code_lines = []
    for i in range(25):
        code_lines.extend([
            f"def function_{i}(param1, param2):",
            f"    '''Docstring for function {i}.'''",
            f"    result = param1 + param2 + {i}",
            f"    return result",
            ""
        ])
    code = "\n".join(code_lines)

    start_time = time.time()
    result = analyzer.analyze(code)
    duration_ms = (time.time() - start_time) * 1000

    assert duration_ms < 100, f"Analysis took {duration_ms}ms, expected < 100ms"
    assert result["performance"]["within_budget"] is True
    print(f"[OK] Performance test passed ({duration_ms:.2f}ms for {len(code_lines)} lines)")


def test_valid_code_no_errors():
    """Test that valid, clean code produces no high-severity errors."""
    code = '''
"""A well-written Python module."""

def calculate_average(numbers: list[float]) -> float:
    """Calculate the arithmetic mean of a list of numbers."""
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def main():
    """Main execution function."""
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    avg = calculate_average(data)
    print(f"Average: {avg}")


if __name__ == "__main__":
    main()
'''
    result = analyzer.analyze(code)

    # Should have no syntax errors
    assert result["has_syntax_errors"] is False

    # Should have no error-level diagnostics
    errors = [d for d in result["diagnostics"] if d["severity"] == "error"]
    assert len(errors) == 0, f"Expected 0 errors, got: {errors}"
    print("[OK] Clean code analysis passed")


def run_all_tests():
    """Run all Phase 1 backend tests."""
    print("\n" + "="*50)
    print("RUNNING PHASE 1 INTEGRATION TESTS")
    print("="*50 + "\n")

    try:
        test_analyzer_syntax_error()
        test_analyzer_undefined_variable()
        test_analyzer_unused_import()
        test_analyzer_pep8_naming()
        test_analyzer_performance()
        test_valid_code_no_errors()

        print("\n" + "="*50)
        print("ALL PHASE 1 BACKEND TESTS PASSED! [SUCCESS]")
        print("="*50 + "\n")
        return True
    except AssertionError as e:
        print("[FAIL] TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] UNEXPECTED ERROR: {e}")
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
