"""Capture API: receive screen frames after explicit consent (FR-19)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.logging import get_logger
from app.vision.screen_pipeline import get_screen_pipeline

logger = get_logger(__name__)

router = APIRouter()


class ManualRegion(BaseModel):
    x: int
    y: int
    w: int
    h: int


class FrameBody(BaseModel):
    frame_b64: str
    consent: bool = False
    # Manual region override: the fallback when detection confidence is low.
    manual_region: ManualRegion | None = None


@router.post("/capture/{session_token}/frame")
async def receive_frame(session_token: str, body: FrameBody) -> dict[str, Any]:
    """Analyze one screen frame. Requires consent=true (tested)."""
    if not body.consent:
        return {"status": "consent_required", "notice": "Capture requires explicit consent."}

    pipeline = get_screen_pipeline(session_token)
    outcome = pipeline.process_frame(
        body.frame_b64,
        manual_region=body.manual_region.model_dump() if body.manual_region else None,
    )
    resp: dict[str, Any] = {
        "status": outcome.status,
        "tracking_state": outcome.tracking_state,
        "region": outcome.region,
        "region_confidence": outcome.region_confidence,
        "ocr_confidence": outcome.ocr_confidence,
        "elapsed_ms": outcome.elapsed_ms,
        "frame_hash": outcome.frame_hash,
    }
    if outcome.notice:
        resp["notice"] = outcome.notice
    if outcome.status == "ok":
        resp["code_length"] = len(outcome.code)
        resp["language"] = outcome.language
        # Reconstructed code goes to the normal analysis flow via the caller.
    return resp
