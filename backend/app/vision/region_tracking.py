from __future__ import annotations

from dataclasses import dataclass

from app.vision.code_region import DetectedRegion


@dataclass
class RegionTracker:
    current: DetectedRegion | None = None

    def update(self, candidate: DetectedRegion | None) -> DetectedRegion | None:
        if candidate is None:
            return self.current

        if self.current is None:
            self.current = candidate
            return candidate

        # Exponential smoothing stabilizes small OCR bounding-box jitter.
        alpha = 0.55
        current = self.current
        self.current = DetectedRegion(
            left=round(alpha * candidate.left + (1 - alpha) * current.left),
            top=round(alpha * candidate.top + (1 - alpha) * current.top),
            width=round(alpha * candidate.width + (1 - alpha) * current.width),
            height=round(alpha * candidate.height + (1 - alpha) * current.height),
            confidence=candidate.confidence,
            code=candidate.code,
        )
        return self.current

    def reset(self) -> None:
        self.current = None
