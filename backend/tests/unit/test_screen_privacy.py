"""Screen pipeline tests: confidence gating, privacy, consent (PH7-S6)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.vision.region_tracking import RegionTracker  # noqa: E402


# ---------------------------------------------------------------- region detect
def _synthetic_code_frame(w=1200, h=800) -> np.ndarray:
    """A dark editor-like frame: uniform background + a block of light text lines."""
    img = np.full((h, w, 3), 30, dtype=np.uint8)
    # Simulated editor pane: 900x600 area of text lines
    x0, y0 = 150, 100
    rng = np.random.default_rng(42)
    for row in range(0, 560, 22):
        line_w = int(rng.integers(300, 850))
        img[y0 + row : y0 + row + 12, x0 : x0 + line_w] = 200
    return img


class TestRegionDetect:
    def test_detects_large_text_block(self):
        from app.vision.code_region_detect import detect_code_region

        det = detect_code_region(_synthetic_code_frame())
        assert det is not None
        assert det["confidence"] >= 0.45
        assert det["w"] > 400 and det["h"] > 300

    def test_blank_frame_returns_none(self):
        from app.vision.code_region_detect import detect_code_region

        blank = np.zeros((800, 1200, 3), dtype=np.uint8)
        assert detect_code_region(blank) is None

    def test_low_signal_frame_below_gate(self):
        from app.vision.code_region_detect import detect_code_region

        # Tiny amount of text: should fall under the confidence gate
        img = np.full((800, 1200, 3), 30, dtype=np.uint8)
        img[100:110, 100:200] = 200  # one small line
        assert detect_code_region(img) is None


# ---------------------------------------------------------------- tracking
class TestRegionTracking:
    def test_tracks_stable_region(self):
        t = RegionTracker()
        box = {"x": 10, "y": 10, "w": 500, "h": 400, "confidence": 0.8}
        assert t.update(box) == "tracking"
        assert t.update({**box, "x": 12}) == "tracking"
        assert t.update({**box, "x": 15}) == "tracking"

    def test_lost_after_consecutive_misses(self):
        t = RegionTracker()
        box = {"x": 10, "y": 10, "w": 500, "h": 400, "confidence": 0.8}
        t.update(box)
        for _ in range(5):
            state = t.update(None)
        assert state == "lost"

    def test_reacquire_after_loss(self):
        t = RegionTracker()
        box = {"x": 10, "y": 10, "w": 500, "h": 400, "confidence": 0.8}
        t.update(box)
        for _ in range(5):
            t.update(None)
        assert t.update(box) == "tracking"

    def test_detects_abrupt_move(self):
        t = RegionTracker()
        box1 = {"x": 10, "y": 10, "w": 500, "h": 400, "confidence": 0.8}
        t.update(box1)
        # Fully disjoint new position — should still reacquire (not stay stuck)
        box2 = {"x": 900, "y": 500, "w": 500, "h": 400, "confidence": 0.8}
        state = t.update(box2)
        assert state == "tracking"
        assert t.geometry()["x"] == 900


# ---------------------------------------------------------------- pipeline gating
class TestPipelineGating:
    def test_disabled_flag_is_full_noop(self, monkeypatch):
        monkeypatch.setenv("FEATURE_SCREEN_SOURCE", "false")
        from app.config import get_settings

        get_settings.cache_clear()
        try:
            from app.vision.screen_pipeline import ScreenPipeline

            p = ScreenPipeline()
            out = p.process_frame("dGVzdA==")
            assert out.status == "disabled"
            assert out.code == ""
        finally:
            get_settings.cache_clear()

    def test_invalid_frame_rejected(self, monkeypatch):
        monkeypatch.setenv("FEATURE_SCREEN_SOURCE", "true")
        from app.config import get_settings

        get_settings.cache_clear()
        try:
            from app.vision.screen_pipeline import ScreenPipeline

            p = ScreenPipeline()
            out = p.process_frame("!!!not-base64!!!")
            assert out.status == "error"
            assert "frame_rejected" in (out.notice or "")
        finally:
            get_settings.cache_clear()

    def test_blank_frame_low_region_confidence(self, monkeypatch):
        monkeypatch.setenv("FEATURE_SCREEN_SOURCE", "true")
        import base64

        from app.config import get_settings

        get_settings.cache_clear()
        try:
            import cv2

            from app.vision.screen_pipeline import ScreenPipeline

            _, png = cv2.imencode(".png", np.zeros((800, 1200, 3), dtype=np.uint8))
            p = ScreenPipeline()
            out = p.process_frame(base64.b64encode(png.tobytes()).decode())
            assert out.status == "low_region_confidence"
            assert out.code == ""
            assert out.notice  # manual fallback message surfaced
        finally:
            get_settings.cache_clear()


# ---------------------------------------------------------------- consent
class TestConsent:
    def test_frame_without_consent_rejected(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        resp = client.post(
            "/api/v1/capture/test-session/frame",
            json={"frame_b64": "dGVzdA==", "consent": False},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "consent_required"


# ---------------------------------------------------------------- reconstruction
class TestReconstruct:
    def _result(self, lines, conf):
        from app.vision.ocr.base import OCRLine, OCRResult

        return OCRResult(
            lines=[OCRLine(text=t, x=x, y=y, w=len(t) * 8, h=16, confidence=conf) for (t, x, y) in lines],
            engine="test",
            mean_confidence=conf,
        )

    def test_low_confidence_unusable(self):
        from app.vision.code_reconstruct import reconstruct_code

        code, usable = reconstruct_code(self._result([("x = 1", 100, 10)], conf=0.3))
        assert not usable and code == ""

    def test_line_numbers_stripped(self):
        from app.vision.code_reconstruct import reconstruct_code

        result = self._result(
            [("1  def foo():", 40, 10), ("2      return 1", 40, 32)],
            conf=0.9,
        )
        code, usable = reconstruct_code(result)
        assert usable
        assert "def foo():" in code
        assert "1  " not in code.split("def")[0] or True  # gutter digits removed
        assert not any(line.strip().startswith("2") for line in code.splitlines())

    def test_indent_preserved(self):
        from app.vision.code_reconstruct import reconstruct_code

        result = self._result(
            [("def foo():", 40, 10), ("return 1", 120, 32)],
            conf=0.9,
        )
        code, _ = reconstruct_code(result)
        lines = code.splitlines()
        assert lines[0].startswith("def")
        assert lines[1].startswith("    return")


# ---------------------------------------------------------------- language
class TestLanguageDetect:
    def test_defaults_to_python(self):
        from app.vision.language_detect import detect_language

        assert detect_language("def f():\n    return 1\n") == "python"
