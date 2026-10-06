"""OpenCV preprocessing for code-region discovery and OCR."""

from __future__ import annotations

import cv2
import numpy as np


def to_grayscale(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def binarize(gray: np.ndarray) -> np.ndarray:
    """Adaptive threshold: robust to themes (dark IDE, light IDE)."""
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 15
    )


def denoise(img: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoising(img, None, h=8, templateWindowSize=7, searchWindowSize=21)


def upscale_for_ocr(img: np.ndarray, target_min_height: int = 800) -> np.ndarray:
    """Upscale small screenshots so OCR models see readable glyph sizes."""
    h = img.shape[0]
    if h >= target_min_height:
        return img
    scale = min(target_min_height / h, 3.0)
    return cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)


def region_geometry(bin_img: np.ndarray) -> list[dict]:
    """Candidate region geometries from text lines.

    Finds text lines, then merges vertically-adjacent lines into blocks so a
    full editor pane (with per-line text) becomes one candidate region.
    """
    # 1. Line-level boxes (small horizontal kernel: merge glyphs into lines)
    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    lines_img = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, line_kernel)
    contours, _ = cv2.findContours(lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h_img, w_img = bin_img.shape[:2]
    line_boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        # Keep text rows/blocks; drop tiny noise and near-full-frame blobs.
        if w < 0.05 * w_img or h < 8 or h > 0.9 * h_img:
            continue
        line_boxes.append((x, y, w, h))

    if not line_boxes:
        return []

    # 2. Merge lines into blocks: union of boxes whose vertical gaps are small
    line_boxes.sort(key=lambda b: b[1])
    merged: list[list[int]] = []
    for x, y, w, h in line_boxes:
        placed = False
        for block in merged:
            bx, by, bw, bh = block
            # Overlapping x-range and small vertical gap -> same block
            x_overlap = min(x + w, bx + bw) - max(x, bx)
            y_gap = max(y, by) - min(y + h, by + bh)
            if x_overlap > 0.3 * min(w, bw) and y_gap < 60:
                nx, ny = min(x, bx), min(y, by)
                block[0], block[1] = nx, ny
                block[2] = max(x + w, bx + bw) - nx
                block[3] = max(y + h, by + bh) - ny
                placed = True
                break
        if not placed:
            merged.append([x, y, w, h])

    boxes = []
    for x, y, w, h in merged:
        area = w * h
        if area < 0.02 * w_img * h_img:
            continue
        # Text blocks can be taller than wide in narrow panes; keep a low floor.
        aspect = w / max(h, 1)
        if aspect < 0.35:
            continue
        boxes.append({"x": x, "y": y, "w": w, "h": h, "area_frac": round(area / (w_img * h_img), 3)})
    boxes.sort(key=lambda b: b["area_frac"], reverse=True)
    return boxes[:6]


def uniform_panes(gray: np.ndarray, min_area_frac: float = 0.08) -> list[dict]:
    """Large uniform-background rectangles (editor panes differ in shade from the UI).

    Editors are big flat regions; detecting them lets us include padding and the
    line-number gutter that a text-pixel bounding box misses.
    """
    h_img, w_img = gray.shape[:2]
    # Quantize shades so subtle pane/background differences collapse into levels,
    # then keep the largest connected component per level.
    levels = (gray // 6).astype(np.uint8)
    panes: list[dict] = []
    for level in np.unique(levels):
        mask = np.uint8(levels == level) * 255
        if np.count_nonzero(mask) < min_area_frac * w_img * h_img:
            continue
        # Clean speckle before components
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
        for i in range(1, n):
            x, y, w, h, area = stats[i]
            if area < min_area_frac * w_img * h_img:
                continue
            aspect = w / max(h, 1)
            if not (0.4 <= aspect <= 5.0):
                continue
            panes.append(
                {"x": int(x), "y": int(y), "w": int(w), "h": int(h), "area_frac": round(area / (w_img * h_img), 3)}
            )
    panes.sort(key=lambda p: p["area_frac"], reverse=True)
    return panes[:4]
