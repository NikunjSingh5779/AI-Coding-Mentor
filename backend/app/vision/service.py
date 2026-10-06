from __future__ import annotations

from app.analysis.pipeline import AnalysisPipeline
from app.config import Settings
from app.vision.code_region import detect_code_region
from app.vision.ocr import decode_image, extract_lines


class ScreenVisionService:
    def __init__(self, settings: Settings, pipeline: AnalysisPipeline) -> None:
        self.settings = settings
        self.pipeline = pipeline

    async def analyze(self, image_bytes: bytes, language: str = "python") -> dict:
        if len(image_bytes) > self.settings.max_frame_bytes:
            raise ValueError("Frame exceeds maximum size")

        image = decode_image(image_bytes)
        if not self.settings.auto_code_discovery_enabled:
            return {
                "detected": False,
                "confidence": 0.0,
                "region": None,
                "code": "",
                "diagnostics": [],
                "notice": "Automatic code discovery is disabled; use the editor source.",
            }

        lines = extract_lines(image, self.settings.ocr_engine)
        region = detect_code_region(
            lines,
            min_confidence=self.settings.region_confidence_gate,
        )
        if region is None:
            return {
                "detected": False,
                "confidence": 0.0,
                "region": None,
                "code": "",
                "diagnostics": [],
                "notice": "No high-confidence code region detected.",
            }

        diagnostics, timings = await self.pipeline.analyze(
            region.code, language=language, seq=0
        )
        return {
            "detected": True,
            "confidence": region.confidence,
            "region": region.as_dict(),
            "code": region.code,
            "diagnostics": [
                {
                    "id": d.id,
                    "seq": d.seq,
                    "origin": d.origin.value,
                    "rule": d.rule,
                    "category": d.category,
                    "severity": d.severity.value,
                    "message": d.message_raw,
                    "range": {
                        "start": {"line": d.range.start.line, "column": d.range.start.col},
                        "end": {"line": d.range.end.line, "column": d.range.end.col},
                    },
                    "fingerprint": d.fingerprint,
                    "confidence": d.confidence,
                }
                for d in diagnostics
            ],
            "stage_timings": timings,
            "notice": None,
        }
