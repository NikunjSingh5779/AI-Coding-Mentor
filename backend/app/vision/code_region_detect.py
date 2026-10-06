"""Automatic code-region detection: rank candidate regions by multi-signal score.

Signals (baseline, deterministic, no ML):
- area (larger text block = more likely the editor)
- edge density (code is text-dense)
- horizontal line structure (code has many short text lines)
- rectangularity (editors are rectangular)

Low overall confidence -> no region (never guess; manual fallback).
"""

from __future__ import annotations

import cv2
import numpy as np

from app.core.logging import get_logger
from app.vision.preprocess import binarize, region_geometry, to_grayscale, uniform_panes

logger = get_logger(__name__)

CONFIDENCE_GATE = 0.45  # below this: return None, surface manual fallback
MIN_AREA_FRAC = 0.03  # a code pane smaller than this is not worth a guess
MIN_PANE_TEXT_COVERAGE = 0.15  # a pane with almost no text rows is just a blank card


def _edge_density(gray: np.ndarray, box: dict) -> float:
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    roi = gray[y : y + h, x : x + w]
    edges = cv2.Canny(roi, 60, 160)
    return float(np.count_nonzero(edges)) / max(w * h, 1)


def _line_structure(binarized: np.ndarray, box: dict) -> float:
    """Fraction of rows in the box that contain text pixels."""
    x, y, w, h = box["x"], box["y"], box["w"], box["h"]
    roi = binarized[y : y + h, x : x + w]
    if roi.size == 0:
        return 0.0
    row_has_text = np.count_nonzero(roi, axis=1) > (w * 0.02)
    return float(np.count_nonzero(row_has_text)) / max(h, 1)


def detect_code_region(img: np.ndarray) -> dict | None:
    """Return the best candidate region + confidence, or None below the gate.

    Output geometry: {"x", "y", "w", "h", "confidence"} in frame pixel coords.
    """
    gray = to_grayscale(img)
    bin_img = binarize(gray)
    h_img, w_img = img.shape[:2]

    # Two candidate families: text blocks (tight) and uniform panes (editor cards).
    candidates = [
        {**box, "kind": "text_block"} for box in region_geometry(bin_img)
    ] + [{**pane, "kind": "pane"} for pane in uniform_panes(gray)]

    if not candidates:
        return None

    scored = []
    for box in candidates:
        if box["area_frac"] < MIN_AREA_FRAC:
            continue  # too small to be an editor pane
        area_score = min(box["area_frac"] / 0.35, 1.0)  # ~35% of frame is typical
        lines = _line_structure(bin_img, box)
        line_score = min(lines / 0.55, 1.0)
        # A pane (or block) with no text rows anywhere is not code: reject it,
        # otherwise a blank/uniform frame would score as a valid region.
        if lines < MIN_PANE_TEXT_COVERAGE:
            continue
        aspect = box["w"] / max(box["h"], 1)
        # Editors are wider than tall; mild preference only.
        rect_score = min(aspect / 2.0, 1.0) if aspect >= 1.2 else min(aspect / 2.0, 0.5)

        if box["kind"] == "pane":
            # A pane is only interesting if it contains real text rows.
            confidence = 0.35 * area_score + 0.50 * line_score + 0.15 * rect_score
        else:
            edge = _edge_density(gray, box)
            edge_score = min(edge / 0.12, 1.0)
            confidence = 0.27 * area_score + 0.20 * edge_score + 0.35 * line_score + 0.18 * rect_score

        scored.append({**box, "confidence": round(confidence, 3)})

    if not scored:
        logger.info("No viable code-region candidate; manual selection required")
        return None

    scored.sort(key=lambda b: b["confidence"], reverse=True)
    best = scored[0]

    if best["confidence"] < CONFIDENCE_GATE:
        logger.info("Region confidence below gate; no diagnostics will be produced")
        return None

    logger.info(
        "Code region detected",
        extra={
            "confidence": best["confidence"],
            "geometry": {k: best[k] for k in ("x", "y", "w", "h")},
            "frame": f"{w_img}x{h_img}",
        },
    )
    return best
