"""Reconstruct code text from OCR line boxes: indentation, gutters, line numbers."""

from __future__ import annotations

import re

from app.vision.ocr.base import OCRResult

# Confidence gate: below this the OCR text is too unreliable to analyze.
OCR_CONFIDENCE_GATE = 0.65

_LINE_NUMBER = re.compile(r"^\s*(\d{1,4}|→|\u21b2)\s+")


def _median_line_height(result: OCRResult) -> float:
    heights = sorted(l.h for l in result.lines)
    if not heights:
        return 0.0
    return heights[len(heights) // 2]


def _estimate_indent(result: OCRResult, line_index: int, base_x: int, unit: int) -> int:
    """Estimate indent level from x-offset relative to the leftmost margin."""
    delta = result.lines[line_index].x - base_x
    return max(0, round(delta / unit)) if unit > 0 else 0


def _indent_geometry(result: OCRResult) -> tuple[int, int]:
    """Return (base margin x, indent unit in px).

    Base margin = leftmost line start (the gutter edge of the code).
    Indent unit = smallest consistent positive x-delta, clamped to a
    plausible range (10-60px) to resist OCR noise.
    """
    if not result.lines:
        return 0, 40
    xs = [l.x for l in result.lines]
    base_x = min(xs)
    deltas = sorted({x - base_x for x in xs if x - base_x > 2})
    unit = deltas[0] if deltas else 40
    unit = max(10, min(60, unit))
    return base_x, unit


def reconstruct_code(result: OCRResult) -> tuple[str, bool]:
    """Rebuild code text from OCR lines.

    Returns (code, usable). usable=False means confidence below the gate:
    the caller must NOT produce diagnostics from this text.
    """
    if not result.lines or result.mean_confidence < OCR_CONFIDENCE_GATE:
        return "", False

    lines_sorted = sorted(result.lines, key=lambda l: (l.y, l.x))
    base_x, unit = _indent_geometry(result)
    out_lines: list[str] = []
    prev_y: int | None = None

    for idx, line in enumerate(lines_sorted):
        text = line.text
        # Strip editor gutters: line numbers and leading arrow markers.
        text = _LINE_NUMBER.sub("", text)
        if not text.strip():
            # Blank line: preserve paragraph breaks but collapse runs.
            if prev_y is not None and out_lines and out_lines[-1] != "":
                out_lines.append("")
            prev_y = line.y
            continue

        indent = _estimate_indent(result, idx, base_x, unit)
        out_lines.append("    " * indent + text.strip())
        prev_y = line.y

    # Trim trailing blanks
    while out_lines and out_lines[-1] == "":
        out_lines.pop()
    return "\n".join(out_lines), True
