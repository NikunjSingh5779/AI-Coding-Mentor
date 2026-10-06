"""Region tracking: follow the selected region across frames, reacquire after loss."""

from __future__ import annotations

from dataclasses import dataclass, field


def _iou(a: dict, b: dict) -> float:
    ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
    bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
    ix = max(0, min(ax2, bx2) - max(a["x"], b["x"]))
    iy = max(0, min(ay2, by2) - max(a["y"], b["y"]))
    inter = ix * iy
    union = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / union if union > 0 else 0.0


TRACKING_IOU = 0.55  # a candidate overlaps the tracked region at/above this IoU
MISS_LIMIT = 5  # consecutive misses before declaring the region lost


@dataclass
class RegionTracker:
    """Tracks the active code region; exposes state for the UI."""

    state: str = "idle"  # idle | tracking | lost
    region: dict | None = None
    _misses: int = 0
    _detections: int = 0
    history: list[dict] = field(default_factory=list)

    def update(self, detection: dict | None) -> str:
        """Feed one frame's detection; returns new state."""
        if detection is None:
            self._misses += 1
            if self.state == "tracking" and self._misses >= MISS_LIMIT:
                self.state = "lost"
            return self.state

        self._misses = 0
        self._detections += 1

        if self.state in ("idle", "lost") or self.region is None:
            self.region = detection
            self.state = "tracking"
        else:
            overlap = _iou(self.region, detection)
            if overlap >= TRACKING_IOU:
                # Smooth-follow: accept the new geometry.
                self.region = detection
            else:
                # Region moved abruptly (window dragged): reacquire.
                self.region = detection
        self.history.append(detection)
        return self.state

    def geometry(self) -> dict | None:
        return self.region
