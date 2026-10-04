"""
Health check API endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy", service="ai-coding-mentor-api", version="0.1.0"
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint."""
    # In later phases, this will check database connectivity, etc.
    return HealthResponse(
        status="ready", service="ai-coding-mentor-api", version="0.1.0"
    )
