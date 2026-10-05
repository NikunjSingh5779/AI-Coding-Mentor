"""
Diagnostics Aggregator: deduplicates, ranks, and fingerprints diagnostics.
Implements issue matching per 03-ARCHITECTURE.md section 5.4.
"""

import hashlib
import re
from typing import List, Dict, Any, Optional
from app.schemas.diagnostic import Diagnostic, Severity
from app.analysis.taxonomy import Category


def compute_fingerprint(
    category: str,
    rule: Optional[str],
    symbol_name: Optional[str],
    line_text: str
) -> str:
    """
    Compute a stable fingerprint for a diagnostic.
    Hash of category, rule, enclosing symbol name, and normalised line text.
    """
    # Normalise whitespace
    norm_line = re.sub(r"\s+", " ", line_text.strip())
    payload = f"{category}|{rule or ''}|{symbol_name or ''}|{norm_line}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def rank_severity(severity: Severity) -> int:
    """Return priority rank for severity (lower is more urgent/severe)."""
    ranks = {
        Severity.ERROR: 1,
        Severity.WARNING: 2,
        Severity.SUSPICION: 3,
        Severity.INFO: 4,
    }
    return ranks.get(severity, 5)


class DiagnosticsAggregator:
    """Aggregates and deduplicates diagnostics from multiple analyzers."""

    def __init__(self):
        pass

    def aggregate(
        self,
        diagnostics: List[Diagnostic],
        code_lines: Optional[List[str]] = None
    ) -> List[Diagnostic]:
        """
        Deduplicate and rank diagnostics.
        - Keeps highest confidence / lowest severity rank per position & category.
        - Updates fingerprints if line text is available.
        - Sorts by line number, column, and severity.
        """
        if not diagnostics:
            return []

        # Deduplication map: key -> Diagnostic
        dedup_map: Dict[str, Diagnostic] = {}

        for diag in diagnostics:
            # Extract line content if available to compute or ensure fingerprint
            line_idx = diag.range.start.line - 1
            line_text = ""
            if code_lines and 0 <= line_idx < len(code_lines):
                line_text = code_lines[line_idx]

            # Generate or preserve fingerprint
            if not diag.fingerprint or diag.fingerprint == "placeholder":
                diag.fingerprint = compute_fingerprint(
                    category=diag.category,
                    rule=diag.rule,
                    symbol_name=None,
                    line_text=line_text
                )

            # Deduplication key based on location and category
            key = f"{diag.range.start.line}:{diag.range.start.col}:{diag.category}"

            if key not in dedup_map:
                dedup_map[key] = diag
            else:
                existing = dedup_map[key]
                # Compare by confidence and severity
                if (diag.confidence > existing.confidence) or (
                    diag.confidence == existing.confidence and
                    rank_severity(diag.severity) < rank_severity(existing.severity)
                ):
                    dedup_map[key] = diag

        result = list(dedup_map.values())

        # Sort primarily by line, then column, then severity rank
        result.sort(key=lambda d: (d.range.start.line, d.range.start.col, rank_severity(d.severity)))

        return result
