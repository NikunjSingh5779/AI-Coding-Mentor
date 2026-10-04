"""
Health Controller - API endpoints for system health checks
Following MVC pattern: Controllers handle request routing and business logic
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import asyncio
import time

from ..core.database import get_db_session
from ..core.config import get_settings

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "service": "ai-coding-screener-api",
        "version": "0.1.0"
    }


@router.get("/health/detailed", response_model=Dict[str, Any])
async def detailed_health_check(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Detailed health check including database connectivity"""
    settings = get_settings()

    # Check database connectivity
    db_healthy = False
    db_latency_ms = None

    try:
        start_time = time.time()
        await db.execute("SELECT 1")
        db_latency_ms = round((time.time() - start_time) * 1000, 2)
        db_healthy = True
    except Exception as e:
        db_healthy = False
        print(f"Database health check failed: {e}")

    # System checks
    checks = {
        "database": {
            "healthy": db_healthy,
            "latency_ms": db_latency_ms
        },
        "llm_config": {
            "provider": settings.llm_provider,
            "model": settings.llm_model_name,
            "configured": bool(settings.llm_local_url or settings.llm_hosted_api_key)
        }
    }

    overall_healthy = all(
        check.get("healthy", True)
        for check in checks.values()
    )

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": int(time.time()),
        "service": "ai-coding-screener-api",
        "version": "0.1.0",
        "checks": checks
    }