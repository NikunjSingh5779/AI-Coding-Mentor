"""
Core FastAPI application for AI Real-Time Coding Screener
Following ICM+MVC pattern: Controllers handle request routing and logic
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from typing import AsyncGenerator

from .core.config import get_settings
from .core.database import init_database, close_database
from .controllers.health_controller import router as health_router
from .controllers.session_controller import router as session_router
from .controllers.mentor_controller import router as mentor_router
from .controllers.analysis_controller import router as analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management"""
    # Startup
    settings = get_settings()
    await init_database(settings.database_url)

    yield

    # Shutdown
    await close_database()


def create_app() -> FastAPI:
    """Application factory following MVC pattern"""
    settings = get_settings()

    app = FastAPI(
        title="AI Real-Time Coding Screener API",
        description="Backend API for AI-powered coding assistance and mentoring",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register controllers (routing layer)
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(session_router, prefix="/api/v1", tags=["sessions"])
    app.include_router(mentor_router, prefix="/api/v1", tags=["mentor"])
    app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )