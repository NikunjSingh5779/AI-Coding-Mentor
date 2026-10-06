"""Screen-source evaluation: region detection metrics + OCR quality.

Region metrics: precision/recall (detected vs ground-truth box, IoU>=0.5),
mean IoU, and gate behavior (no detection below confidence gate).
OCR metrics: line accuracy (normalized lines matched), CER on matched lines.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

root_dir = Path(__file__).resolve().parent.parent.parent
for p in (str(root_dir / "backend"), str(Path(__file__).resolve().parent.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.vision import preprocess as vp  # noqa: E402
from app.vision.code_region_detect import detect_code_region  # noqa: E402
from app.vision.code_reconstruct import reconstruct_code  # noqa: E402
from app.vision.ocr.base import get_ocr_engine  # noqa: E402
from harness.report import save_report  # noqa: E402

EVAL_DIR = root_dir / "eval" / "datasets"
IOU_MATCH = 0.5


def iou(a: dict, b: dict) -> float:
    ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
    bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
    ix = max(0, min(ax2, bx2) - max(a["x"], b["x"]))
    iy = max(0, min(ay2, by2) - max(a["y"], b["y"]))
    inter = ix * iy
    union = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / union if union else 0.0


def _cer(ref: str, hyp: str) -> float:
    """Character error rate via edit distance."""
    import collections

    d = collections.defaultdict(int)
    for i in range(len(ref) + 1):
        d[(i, 0)] = i
    for j in range(len(hyp) + 1):
        d[(0, j)] = j
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[(i, j)] = min(d[(i - 1, j)] + 1, d[(i, j - 1)] + 1, d[(i - 1, j - 1)] + cost)
    return d[(len(ref), len(hyp))] / max(len(ref), 1)


def eval_regions() -> dict:
    cases = sorted((EVAL_DIR / "code_regions").glob("*.json"))
    tp = fp = fn = 0
    ious = []
    for case in cases:
        meta = json.loads(case.read_text())
        img = cv2.imread(str(case.parent / meta["image"]))
        det = detect_code_region(img)
        gt = meta["ground_truth_region"]
        if det is None:
            fn += 1
            continue
        score = iou(det, gt)
        ious.append(score)
        if score >= IOU_MATCH:
            tp += 1
        else:
            fp += 1
            fn += 1
    n_gt = tp + fn
    return {
        "cases": len(cases),
        "precision": round(tp / (tp + fp), 3) if tp + fp else 0.0,
        "recall": round(tp / n_gt, 3) if n_gt else 0.0,
        "mean_iou": round(sum(ious) / len(ious), 3) if ious else 0.0,
    }


def eval_ocr() -> dict:
    cases = sorted((EVAL_DIR / "ocr_screens").glob("*.json"))
    engine = get_ocr_engine()
    line_accs: list[float] = []
    cers: list[float] = []
    usable = 0
    for case in cases:
        meta = json.loads(case.read_text())
        img = cv2.imread(str(case.parent / meta["image"]))
        gray = vp.upscale_for_ocr(vp.to_grayscale(img))
        result = engine.recognize(gray)
        code, ok = reconstruct_code(result)
        if not ok:
            continue
        usable += 1

        ref_lines = [l.strip() for l in meta["ground_truth_text"].splitlines() if l.strip()]
        hyp_lines = [l.strip() for l in code.splitlines() if l.strip()]
        matched = sum(
            1
            for hl in hyp_lines
            if any(
                hl.replace(" ", "") in rl.replace(" ", "") or rl.replace(" ", "") in hl.replace(" ", "")
                for rl in ref_lines
            )
        )
        # Normalize by the larger line count so a noisy reconstruction
        # (splitting one line into several) cannot exceed 1.0.
        denominator = max(len(ref_lines), len(hyp_lines), 1)
        line_accs.append(min(matched / denominator, 1.0))

        ref_join = "".join(ref_lines).replace(" ", "")
        hyp_join = "".join(hyp_lines).replace(" ", "")
        cers.append(_cer(ref_join, hyp_join))

    n = len(cases)
    return {
        "cases": n,
        "usable_after_gate": usable,
        "line_accuracy": round(sum(line_accs) / len(line_accs), 3) if line_accs else 0.0,
        "cer": round(sum(cers) / len(cers), 3) if cers else 1.0,
    }


if __name__ == "__main__":
    print("Evaluating code-region detection...")
    region_report = eval_regions()
    print(json.dumps(region_report, indent=2))

    print("Evaluating OCR (this loads the OCR model)...")
    ocr_report = eval_ocr()
    print(json.dumps(ocr_report, indent=2))

    save_report({"suite": "screen", "regions": region_report, "ocr": ocr_report}, "screen_eval")
