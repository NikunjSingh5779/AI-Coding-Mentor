from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CodeRegion:
    left: int
    top: int
    width: int
    height: int
    confidence: float

    def as_dict(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }
