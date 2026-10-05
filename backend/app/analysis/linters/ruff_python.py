"""
Ruff Python Linter Wrapper.
Executes Ruff subprocess on stdin with JSON output format and maps findings to taxonomy.
"""

import json
import shutil
import subprocess
import uuid
from typing import List, Optional
from app.schemas.diagnostic import Diagnostic, DiagnosticRange, Position, Severity, Origin
from app.analysis.taxonomy import map_rule_to_category, CATEGORY_METADATA
from app.analysis.aggregator import compute_fingerprint
from app.analysis.linters.base import BaseLinter


class RuffPythonLinter(BaseLinter):
    """Linter wrapper for Ruff static analysis tool on Python code."""

    def __init__(self, ruff_path: Optional[str] = None):
        self.ruff_bin = ruff_path or shutil.which("ruff") or "ruff"

    def is_available(self) -> bool:
        """Check if ruff is available on PATH."""
        return shutil.which(self.ruff_bin) is not None or shutil.which("ruff") is not None

    def lint(
        self,
        code: str,
        filename: str = "snippet.py",
        seq: int = 0,
        timeout_seconds: float = 2.0
    ) -> List[Diagnostic]:
        """
        Run Ruff on code string via subprocess.
        """
        if not code or not code.strip():
            return []

        # Select relevant rules for learner linting (Pyflakes, pycodestyle errors/warnings, naming)
        cmd = [
            self.ruff_bin,
            "check",
            "--select", "E,W,F,N",
            "--output-format=json",
            f"--stdin-filename={filename}",
            "-"
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            stdout, _ = process.communicate(input=code, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            return []
        except Exception:
            return []

        if not stdout or not stdout.strip():
            return []

        try:
            items = json.loads(stdout)
        except Exception:
            return []

        diagnostics: List[Diagnostic] = []
        code_lines = code.splitlines()

        for item in items:
            rule = item.get("code")
            msg = item.get("message", "Lint warning")
            loc = item.get("location", {})
            end_loc = item.get("end_location", {})

            line = loc.get("row", 1)
            col = loc.get("column", 1)
            end_line = end_loc.get("row", line)
            end_col = end_loc.get("column", col + 1)

            category = map_rule_to_category(rule)
            meta = CATEGORY_METADATA.get(category)
            sev_str = meta.default_severity if meta else "warning"

            # Map severity string to Severity enum
            try:
                severity = Severity(sev_str)
            except ValueError:
                severity = Severity.WARNING

            line_text = code_lines[line - 1] if 0 <= line - 1 < len(code_lines) else ""
            fp = compute_fingerprint(
                category=category.value,
                rule=rule,
                symbol_name=None,
                line_text=line_text
            )

            diagnostics.append(
                Diagnostic(
                    id=str(uuid.uuid4()),
                    seq=seq,
                    origin=Origin.LINTER,
                    rule=rule,
                    category=category.value,
                    severity=severity,
                    message_raw=f"[{rule}] {msg}" if rule else msg,
                    range=DiagnosticRange(
                        start=Position(line=line, col=col),
                        end=Position(line=end_line, col=end_col)
                    ),
                    fingerprint=fp,
                    confidence=0.95
                )
            )

        return diagnostics
