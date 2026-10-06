"""Screen pipeline: frame -> region -> OCR -> reconstructed code (gated).

Privacy invariants enforced here:
- FEATURE_SCREEN_SOURCE=false: everything is a no-op.
- Low region confidence or low OCR confidence: NO code text is returned
  and NO diagnostics may be produced (source.notice instead).
- Frames and raw OCR text are never persisted or logged (only hashes/lengths).
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from app.config import get_settings
from app.core.logging import get_logger
from app.vision import code_region_detect
from app.vision import preprocess as vp
from app.vision.code_reconstruct import reconstruct_code
from app.vision.frame_decode import FrameError, decode_frame
from app.vision.ocr.base import get_ocr_engine
from app.vision.region_tracking import RegionTracker

logger = get_logger(__name__)


@dataclass
class ScreenAnalysisOutcome:
    """Result of one screen frame analysis. Carries data, never frames."""

    status: str  # ok | low_region_confidence | low_ocr_confidence | disabled | error
    code: str = ""
    language: str = "python"
    region: dict | None = None
    tracking_state: str = "idle"
    region_confidence: float = 0.0
    ocr_confidence: float = 0.0
    elapsed_ms: float = 0.0
    frame_hash: str = ""  # hash only — never the frame itself
    notice: str | None = None


class ScreenPipeline:
    """Stateful per-session pipeline (owns the region tracker)."""

    def __init__(self):
        self.tracker = RegionTracker()

    def process_frame(self, frame_b64: str, manual_region: dict | None = None) -> ScreenAnalysisOutcome:
        settings = get_settings()
        t0 = time.perf_counter()
        frame_hash = hashlib.sha256(frame_b64[:256].encode()).hexdigest()[:12]

        if not settings.feature_screen_source:
            return ScreenAnalysisOutcome(status="disabled", frame_hash=frame_hash)

        try:
            img = decode_frame(frame_b64)
        except FrameError as exc:
            logger.info("Frame rejected", extra={"reason": str(exc), "frame_hash": frame_hash})
            return ScreenAnalysisOutcome(status="error", notice=f"frame_rejected: {exc}", frame_hash=frame_hash)

        # 1. Region discovery / tracking. A manual region overrides detection
        #    entirely (the documented fallback when confidence is low).
        if manual_region:
            h_img, w_img = img.shape[:2]
            detection = {
                "x": max(0, int(manual_region.get("x", 0))),
                "y": max(0, int(manual_region.get("y", 0))),
                "w": min(int(manual_region.get("w", 0)), w_img),
                "h": min(int(manual_region.get("h", 0)), h_img),
                "area_frac": 0.0,
                "confidence": 1.0,
                "manual": True,
            }
            if detection["w"] < 50 or detection["h"] < 50:
                return ScreenAnalysisOutcome(
                    status="error", notice="invalid_manual_region", frame_hash=frame_hash
                )
            self.tracker.state = "tracking"
            self.tracker.region = detection
            tracking_state = "tracking"
        else:
            detection = code_region_detect.detect_code_region(img)
            tracking_state = self.tracker.update(detection)
        if detection is None or tracking_state == "lost":
            return ScreenAnalysisOutcome(
                status="low_region_confidence",
                tracking_state=tracking_state,
                notice="Cannot reliably locate the code area — select it manually or reposition the window.",
                frame_hash=frame_hash,
                elapsed_ms=round((time.perf_counter() - t0) * 1000, 1),
            )

        # 2. Crop + preprocess for OCR
        x, y, w, h = detection["x"], detection["y"], detection["w"], detection["h"]
        roi = img[y : y + h, x : x + w]
        gray = vp.to_grayscale(roi)
        gray = vp.upscale_for_ocr(gray)

        # 3. OCR
        try:
            ocr = get_ocr_engine().recognize(gray)
        except Exception as exc:
            logger.warning("OCR engine failure", extra={"error": str(exc), "frame_hash": frame_hash})
            return ScreenAnalysisOutcome(
                status="error",
                notice="ocr_engine_failure",
                tracking_state=tracking_state,
                region=detection,
                frame_hash=frame_hash,
            )

        # 4. Reconstruct (gated by OCR confidence inside)
        code, usable = reconstruct_code(ocr)
        elapsed = round((time.perf_counter() - t0) * 1000, 1)

        if not usable:
            return ScreenAnalysisOutcome(
                status="low_ocr_confidence",
                tracking_state=tracking_state,
                region=detection,
                region_confidence=detection["confidence"],
                ocr_confidence=round(ocr.mean_confidence, 3),
                notice="Screen text too unclear to analyze safely — no diagnostics will be produced.",
                frame_hash=frame_hash,
                elapsed_ms=elapsed,
            )

        # 5. Language guess
        from app.vision.language_detect import detect_language

        language = detect_language(code)

        logger.info(
            "Screen frame analyzed",
            extra={
                "frame_hash": frame_hash,
                "region_confidence": detection["confidence"],
                "ocr_confidence": round(ocr.mean_confidence, 3),
                "code_chars": len(code),
                "elapsed_ms": elapsed,
            },
        )
        return ScreenAnalysisOutcome(
            status="ok",
            code=code,
            language=language,
            region=detection,
            tracking_state=tracking_state,
            region_confidence=detection["confidence"],
            ocr_confidence=round(ocr.mean_confidence, 3),
            frame_hash=frame_hash,
            elapsed_ms=elapsed,
        )


_pipelines: dict[str, ScreenPipeline] = {}


def get_screen_pipeline(session_token: str) -> ScreenPipeline:
    if session_token not in _pipelines:
        _pipelines[session_token] = ScreenPipeline()
    return _pipelines[session_token]


def reset_screen_pipelines() -> None:
    _pipelines.clear()
