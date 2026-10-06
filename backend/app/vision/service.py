from __future__ import annotations

from PIL import Image

from app.analysis.pipeline import AnalysisPipeline
from app.config import Settings
from app.vision.code_region import DetectedRegion, detect_code_region
from app.vision.ocr import decode_image, extract_lines
from app.vision.region_tracking import RegionTracker


class ScreenVisionService:
    def __init__(self, settings: Settings, pipeline: AnalysisPipeline) -> None:
        self.settings = settings
        self.pipeline = pipeline
        self.trackers: dict[str, RegionTracker] = {}

    @staticmethod
    def _crop(image: Image.Image, region: dict[str, int]) -> Image.Image:
        left = max(0, int(region.get("left", 0)))
        top = max(0, int(region.get("top", 0)))
        width = max(1, int(region.get("width", 1)))
        height = max(1, int(region.get("height", 1)))
        right = min(image.width, left + width)
        bottom = min(image.height, top + height)
        return image.crop((left, top, right, bottom))

    async def analyze(
        self,
        image_bytes: bytes,
        language: str = "python",
        manual_region: dict[str, int] | None = None,
        session_key: str = 'default',
    ) -> dict:
        if len(image_bytes) > self.settings.max_frame_bytes:
            raise ValueError("Frame exceeds maximum size")

        image = decode_image(image_bytes)

        if manual_region:
            crop = self._crop(image, manual_region)
            lines = extract_lines(crop, self.settings.ocr_engine)
            base_left = min((line.left for line in lines), default=0)
            code = "\n".join(
                (" " * min(32, max(0, round((line.left - base_left) / 10))))
                + line.text
                for line in lines
            )
            confidence = (
                sum(line.confidence for line in lines) / len(lines)
                if lines else 0.0
            )
            region = DetectedRegion(
                left=int(manual_region.get("left", 0)),
                top=int(manual_region.get("top", 0)),
                width=int(manual_region.get("width", crop.width)),
                height=int(manual_region.get("height", crop.height)),
                confidence=min(1.0, confidence),
                code=code,
            )
            self.trackers[session_key] = RegionTracker(current=region)
        else:
            if not self.settings.auto_code_discovery_enabled:
                self.trackers.pop(session_key, None)
                return {
                    "detected": False,
                    "confidence": 0.0,
                    "region": None,
                    "code": "",
                    "diagnostics": [],
                    "notice": "Automatic code discovery is disabled. Choose a manual region.",
                }

            lines = extract_lines(image, self.settings.ocr_engine)
            candidate = detect_code_region(
                lines,
                min_confidence=self.settings.region_confidence_gate,
            )
            tracker = self.trackers.setdefault(session_key, RegionTracker())
            region = tracker.update(candidate)
            if region is None:
                return {
                    "detected": False,
                    "confidence": 0.0,
                    "region": None,
                    "code": "",
                    "diagnostics": [],
                    "notice": "No high-confidence code region detected. Try a manual region.",
                }

        if region.confidence < self.settings.region_confidence_gate:
            return {
                "detected": False,
                "confidence": region.confidence,
                "region": region.as_dict(),
                "code": "",
                "diagnostics": [],
                "notice": "Region confidence is below the safety gate; no diagnostics were emitted.",
            }

        diagnostics, timings = await self.pipeline.analyze(
            region.code,
            language=language,
            seq=0,
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
