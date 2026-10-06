from __future__ import annotations

import time

import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.core.database import AsyncSessionLocal
from app.mentor.client import MentorClient


router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, object]:
    return {
        "status": "healthy",
        "service": "ai-coding-mentor-api",
        "version": "1.0.0",
        "timestamp": int(time.time()),
    }


@router.get("/ready")
async def readiness_check() -> dict[str, object]:
    settings = get_settings()
    checks: dict[str, dict[str, object]] = {}

    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        checks["database"] = {"healthy": True}
    except Exception as exc:
        checks["database"] = {"healthy": False, "error": type(exc).__name__}

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(settings.sandbox_url.rstrip("/") + "/health")
            checks["sandbox"] = {"healthy": response.is_success}
    except Exception as exc:
        checks["sandbox"] = {"healthy": False, "error": type(exc).__name__}

    checks["llm"] = {
        "healthy": not settings.llm_enabled or bool(settings.llm_base_url),
        "enabled": settings.llm_enabled,
        "model": settings.llm_model,
    }

    healthy = all(bool(item.get("healthy")) for item in checks.values())
    return {
        "status": "ready" if healthy else "degraded",
        "service": "ai-coding-mentor-api",
        "checks": checks,
        "timestamp": int(time.time()),
    }
