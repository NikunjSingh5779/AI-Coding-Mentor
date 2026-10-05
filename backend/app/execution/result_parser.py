"""
Parser that turns sandbox execution results and tracebacks into runtime Diagnostics.
Maps exception types and statuses to taxonomy categories per 03-ARCHITECTURE.md section 9.6.
"""

import hashlib
import re
from typing import List, Optional, Tuple

from app.analysis.taxonomy import Category
from app.schemas.diagnostic import (
    Diagnostic,
    DiagnosticRange,
    Origin,
    Position,
    Severity,
)

# Exception type to Taxonomy Category mapping
EXCEPTION_CATEGORY_MAP = {
    "ZeroDivisionError": Category.RUNTIME_ZERO_DIVISION,
    "IndexError": Category.RUNTIME_INDEX,
    "KeyError": Category.RUNTIME_KEY,
    "RecursionError": Category.RUNTIME_RECURSION,
    "TypeError": Category.TYPE_MISMATCH,
    "NameError": Category.NAME_UNDEFINED,
    "AttributeError": Category.RUNTIME_NULL,
    "ModuleNotFoundError": Category.ENV_UNSUPPORTED,
    "ImportError": Category.IMPORT_UNRESOLVED,
    "TimeoutError": Category.RUNTIME_TIMEOUT,
    "MemoryError": Category.RUNTIME_MEMORY,
    "FileNotFoundError": Category.RUNTIME_OTHER,
    "ValueError": Category.RUNTIME_OTHER,
    "StopIteration": Category.RUNTIME_OTHER,
}

# Regex to match traceback file lines
TRACEBACK_LINE_REGEX = re.compile(
    r'File\s+["\'](?P<file>[^"\']+)["\'],\s+line\s+(?P<line>\d+)(?:,\s+in\s+(?P<func>[^\n]+))?'
)

# Regex to match exception name and message
EXCEPTION_LINE_REGEX = re.compile(
    r'^(?P<exc_type>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Exit|Interrupt|Warning|Iteration)):\s*(?P<msg>.*)$'
)


def extract_traceback_info(stderr: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Extract the last line number in learner code, exception type, and message from stderr.
    Returns (line_number, exc_type, message).
    """
    if not stderr:
        return None, None, None

    lines = stderr.strip().splitlines()
    last_line_num = None
    exc_type = None
    exc_msg = None

    # Find traceback file occurrences
    for line in lines:
        match = TRACEBACK_LINE_REGEX.search(line)
        if match:
            filename = match.group("file")
            # We care about main.py or learner scripts
            if "main.py" in filename or not filename.startswith("/usr"):
                try:
                    last_line_num = int(match.group("line"))
                except ValueError:
                    pass

    # Check last lines for Exception name
    for line in reversed(lines):
        line_str = line.strip()
        match = EXCEPTION_LINE_REGEX.match(line_str)
        if match:
            exc_type = match.group("exc_type")
            exc_msg = match.group("msg")
            break
        if line_str.endswith("Error") and " " not in line_str:
            exc_type = line_str
            exc_msg = ""
            break

    return last_line_num, exc_type, exc_msg


def compute_runtime_fingerprint(category: str, line: int, message: str) -> str:
    """Generate stable fingerprint for a runtime diagnostic."""
    raw = f"runtime:{category}:{line}:{message[:60]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def parse_execution_result_to_diagnostics(
    status: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    code: str = "",
) -> List[Diagnostic]:
    """
    Convert raw runner output into a structured list of runtime Diagnostics.
    """
    diagnostics: List[Diagnostic] = []

    # 1. Handle Timeout Status
    if status == "timeout":
        msg = "Execution timed out (infinite loop or blocked operation)"
        diag_id = f"runtime_timeout_1"
        diagnostics.append(
            Diagnostic(
                id=diag_id,
                origin=Origin.RUNTIME,
                category=Category.RUNTIME_TIMEOUT.value,
                severity=Severity.ERROR,
                message_raw=msg,
                range=DiagnosticRange(
                    start=Position(line=1, col=1),
                    end=Position(line=1, col=1),
                ),
                fingerprint=compute_runtime_fingerprint(Category.RUNTIME_TIMEOUT.value, 1, msg),
                confidence=1.0,
            )
        )
        return diagnostics

    # 2. Handle Memory Limit / OOM Status
    if status == "memory_limit" or exit_code == 137:
        msg = "Process exceeded memory limit (Out of Memory)"
        diag_id = f"runtime_oom_1"
        diagnostics.append(
            Diagnostic(
                id=diag_id,
                origin=Origin.RUNTIME,
                category=Category.RUNTIME_MEMORY.value,
                severity=Severity.ERROR,
                message_raw=msg,
                range=DiagnosticRange(
                    start=Position(line=1, col=1),
                    end=Position(line=1, col=1),
                ),
                fingerprint=compute_runtime_fingerprint(Category.RUNTIME_MEMORY.value, 1, msg),
                confidence=1.0,
            )
        )
        return diagnostics

    # 3. Handle Python Exceptions from Stderr
    if exit_code != 0 and stderr:
        line_num, exc_type, exc_msg = extract_traceback_info(stderr)
        line = line_num if line_num is not None and line_num > 0 else 1

        # Map category
        if exc_type and exc_type in EXCEPTION_CATEGORY_MAP:
            category = EXCEPTION_CATEGORY_MAP[exc_type].value
        else:
            category = Category.RUNTIME_OTHER.value

        # Tailor message
        if exc_type and exc_msg:
            full_msg = f"{exc_type}: {exc_msg}"
        elif exc_type:
            full_msg = exc_type
        else:
            full_msg = stderr.strip().splitlines()[-1] if stderr.strip() else "Runtime error occurred"

        diag_id = f"runtime_{category}_{line}"
        diagnostics.append(
            Diagnostic(
                id=diag_id,
                origin=Origin.RUNTIME,
                category=category,
                severity=Severity.ERROR,
                message_raw=full_msg,
                range=DiagnosticRange(
                    start=Position(line=line, col=1),
                    end=Position(line=line, col=1),
                ),
                fingerprint=compute_runtime_fingerprint(category, line, full_msg),
                confidence=1.0,
            )
        )

    return diagnostics
