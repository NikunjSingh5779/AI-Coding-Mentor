"""
AI Real-Time Coding Screener - Main FastAPI Application

This is the composition root that wires all modules together and creates
the FastAPI application with WebSocket support for real-time code analysis.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.config import get_settings
from app.core.errors import AppError
from app.core.events import EventBus
from app.core.logging import get_logger, setup_logging
from app.ws.endpoint import websocket_endpoint

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown tasks."""
    settings = get_settings()
    logger.info("Starting AI Coding Mentor application", extra={"version": "0.1.0"})

    # Initialize event bus
    event_bus = EventBus()
    app.state.event_bus = event_bus

    # Log configuration
    logger.info(
        "Application configured",
        extra={
            "debug": settings.debug,
            "cors_origins": settings.cors_origins,
            "feature_screen_source": settings.feature_screen_source,
        },
    )

    yield

    # Cleanup
    logger.info("Shutting down AI Coding Mentor application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Setup structured logging
    setup_logging(settings.log_level, settings.debug)

    app = FastAPI(
        title="AI Real-Time Coding Screener",
        description="Real-time code analysis with progressive mentoring hints",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(AppError)
    async def app_error_handler(request, exc: AppError):
        logger.error(
            "Application error",
            extra={
                "error_type": type(exc).__name__,
                "message": str(exc),
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "type": exc.error_type},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger.exception("Unhandled exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "type": "internal_error"},
        )

    # Include routers
    app.include_router(health_router, prefix="/api/v1", tags=["health"])

    # WebSocket endpoint
    app.websocket("/ws")(websocket_endpoint)

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use our custom logging setup
    )
