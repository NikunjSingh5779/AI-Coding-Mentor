"""
Unit tests for runtime execution result parsing and traceback extraction.
"""

from app.analysis.taxonomy import Category
from app.execution.result_parser import (
    extract_traceback_info,
    parse_execution_result_to_diagnostics,
)
from app.schemas.diagnostic import Origin, Severity


def test_extract_traceback_zero_division():
    """Test extracting ZeroDivisionError from a traceback."""
    stderr = """
Traceback (most recent call last):
  File "main.py", line 15, in <module>
    main()
  File "main.py", line 8, in calculate
    return 100 / divisor
ZeroDivisionError: division by zero
"""
    line, exc_type, exc_msg = extract_traceback_info(stderr)
    assert line == 8
    assert exc_type == "ZeroDivisionError"
    assert exc_msg == "division by zero"


def test_extract_traceback_index_error():
    """Test extracting IndexError from nested frames."""
    stderr = """
Traceback (most recent call last):
  File "/work/main.py", line 22, in <module>
    val = get_item(5)
  File "/work/main.py", line 4, in get_item
    return items[idx]
IndexError: list index out of range
"""
    line, exc_type, exc_msg = extract_traceback_info(stderr)
    assert line == 4
    assert exc_type == "IndexError"
    assert exc_msg == "list index out of range"


def test_parse_zero_division_diagnostic():
    """Test mapping ZeroDivisionError to RUNTIME_ZERO_DIVISION diagnostic."""
    stderr = """
Traceback (most recent call last):
  File "main.py", line 12, in <module>
    x = 1 / 0
ZeroDivisionError: division by zero
"""
    diagnostics = parse_execution_result_to_diagnostics(
        status="error",
        exit_code=1,
        stdout="",
        stderr=stderr,
    )
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.origin == Origin.RUNTIME
    assert diag.severity == Severity.ERROR
    assert diag.category == Category.RUNTIME_ZERO_DIVISION.value
    assert diag.range.start.line == 12
    assert "ZeroDivisionError" in diag.message_raw


def test_parse_timeout_diagnostic():
    """Test mapping timeout status to RUNTIME_TIMEOUT diagnostic."""
    diagnostics = parse_execution_result_to_diagnostics(
        status="timeout",
        exit_code=-1,
        stdout="",
        stderr="Execution timed out after 5.0 seconds",
    )
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.category == Category.RUNTIME_TIMEOUT.value
    assert diag.severity == Severity.ERROR


def test_parse_oom_diagnostic():
    """Test mapping memory limit status to RUNTIME_MEMORY diagnostic."""
    diagnostics = parse_execution_result_to_diagnostics(
        status="memory_limit",
        exit_code=137,
        stdout="",
        stderr="Process killed (Memory limit exceeded)",
    )
    assert len(diagnostics) == 1
    diag = diagnostics[0]
    assert diag.category == Category.RUNTIME_MEMORY.value
    assert diag.severity == Severity.ERROR
