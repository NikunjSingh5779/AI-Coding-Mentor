"""OCR engine interface + RapidOCR implementation (bake-off winner: no system binary).

The interface allows swapping engines (Tesseract, vision-language models)
without touching the pipeline. All engines return lines with geometry so
code_reconstruct can rebuild indentation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OCRLine:
    """One recognized text line with its bounding box."""

    text: str
    x: int
    y: int
    w: int
    h: int
    confidence: float


@dataclass
class OCRResult:
    """Full OCR output for one region."""

    lines: list[OCRLine] = field(default_factory=list)
    engine: str = "rapidocr"
    mean_confidence: float = 0.0
    elapsed_ms: float = 0.0


class OCREngine(ABC):
    """Interface every OCR backend implements."""

    name: str = "base"

    @abstractmethod
    def recognize(self, img: np.ndarray) -> OCRResult:
        """Recognize text lines in a BGR image (or grayscale converted inside)."""


class RapidOCREngine(OCREngine):
    """RapidOCR (ONNX Runtime): pip-installable, no system binaries, CPU."""

    name = "rapidocr"

    def __init__(self):
        from rapidocr_onnxruntime import RapidOCR

        self._engine = RapidOCR()

    def recognize(self, img: np.ndarray) -> OCRResult:
        import time

        t0 = time.perf_counter()
        result, _ = self._engine(img)
        elapsed = (time.perf_counter() - t0) * 1000

        lines: list[OCRLine] = []
        if result:
            for box, text, conf in result:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                lines.append(
                    OCRLine(
                        text=str(text),
                        x=int(min(xs)),
                        y=int(min(ys)),
                        w=int(max(xs) - min(xs)),
                        h=int(max(ys) - min(ys)),
                        confidence=float(conf),
                    )
                )
        mean_conf = sum(line.confidence for line in lines) / len(lines) if lines else 0.0
        return OCRResult(lines=lines, engine=self.name, mean_confidence=mean_conf, elapsed_ms=round(elapsed, 1))


_engine: OCREngine | None = None


def get_ocr_engine() -> OCREngine:
    global _engine
    if _engine is None:
        _engine = RapidOCREngine()
    return _engine


def reset_ocr_engine() -> None:
    global _engine
    _engine = None
