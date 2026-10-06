from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.vision.service import ScreenVisionService
from app.analysis.pipeline import AnalysisPipeline

router = APIRouter(prefix="/screen", tags=["screen"])

_pipeline = AnalysisPipeline()


@router.post("/analyze")
async def analyze_screen(
    session_token: str,
    language: str = "python",
    frame: UploadFile = File(...),
) -> dict:
    settings = get_settings()
    if not settings.feature_screen_source:
        raise HTTPException(403, "Screen source is disabled")
    if not frame.content_type or not frame.content_type.startswith("image/"):
        raise HTTPException(415, "A raster image is required")
    data = await frame.read()
    if len(data) > settings.max_frame_bytes:
        raise HTTPException(413, "Frame exceeds configured limit")

    try:
        return await ScreenVisionService(settings, _pipeline).analyze(
            data, language=language
        )
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
