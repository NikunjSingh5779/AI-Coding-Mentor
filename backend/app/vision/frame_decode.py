"""Frame decode and validation for incoming screen captures."""

from __future__ import annotations

import base64
import binascii

import cv2
import numpy as np

from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_FRAME_BYTES = 8 * 1024 * 1024  # 8 MB per frame
ALLOWED_MIN_DIM = 200
ALLOWED_MAX_DIM = 4096


class FrameError(ValueError):
    """Invalid or undecodable frame."""


def decode_frame(data_b64: str) -> np.ndarray:
    """Decode a base64-encoded image (png/jpeg) into a BGR ndarray.

    Raises FrameError on bad input. Never logs the frame content.
    """
    if not data_b64 or len(data_b64) > MAX_FRAME_BYTES:
        raise FrameError("frame too large or empty")

    try:
        raw = base64.b64decode(data_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise FrameError("invalid base64") from exc

    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise FrameError("undecodable image")

    h, w = img.shape[:2]
    if not (ALLOWED_MIN_DIM <= w <= ALLOWED_MAX_DIM and ALLOWED_MIN_DIM <= h <= ALLOWED_MAX_DIM):
        raise FrameError(f"frame dimensions out of range: {w}x{h}")

    return img
