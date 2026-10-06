from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.core.database import get_db_session
from app.persistence.service import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.vision.service import ScreenVisionService
from app.analysis.pipeline import AnalysisPipeline

router = APIRouter(prefix="/screen", tags=["screen"])

_pipeline = AnalysisPipeline()
_vision = ScreenVisionService(get_settings(), _pipeline)


@router.post("/analyze")
async def analyze_screen(
    session_token: str,
    language: str = "python",
    frame: UploadFile = File(...),
    region_left: int | None = Form(default=None),
    region_top: int | None = Form(default=None),
    region_width: int | None = Form(default=None),
    region_height: int | None = Form(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    settings = get_settings()
    screen_session = await get_session(db, session_token)
    if screen_session is None or not screen_session.is_active:
        raise HTTPException(404, "Session not found")
    if not settings.feature_screen_source:
        raise HTTPException(403, "Screen source is disabled")
    if not frame.content_type or not frame.content_type.startswith("image/"):
        raise HTTPException(415, "A raster image is required")
    data = await frame.read()
    if len(data) > settings.max_frame_bytes:
        raise HTTPException(413, "Frame exceeds configured limit")

    try:
        manual_region = None
        if None not in (region_left, region_top, region_width, region_height):
            manual_region = {
                "left": max(0, int(region_left)),
                "top": max(0, int(region_top)),
                "width": max(1, int(region_width)),
                "height": max(1, int(region_height)),
            }
        return await _vision.analyze(
            data, language=language, manual_region=manual_region
        )
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
