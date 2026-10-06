"""
AI Real-Time Coding Screener - Main FastAPI Application

This is the composition root that wires all modules together and creates
the FastAPI application with WebSocket support for real-time code analysis.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.capture import router as capture_router
from app.api.health import router as health_router
from app.api.hints import router as hints_router
from app.api.history import router as history_router
from app.api.problems import router as problems_router
from app.api.progress import router as progress_router
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

    # Initialize the database pool. A database outage must NOT stop the API:
    # the session still runs in memory and persistence degrades gracefully
    # (see the database-stopped drill in docs/08-ROLLBACK-AND-FAILURE-HANDLING.md).
    try:
        from app.core.database import close_database, init_database

        await init_database(settings.database_url)
        app.state.db_ready = True
    except Exception as exc:  # noqa: BLE001 - degrade instead of crashing on boot
        app.state.db_ready = False
        logger.warning(
            "Database unavailable at startup; running without persistence",
            extra={"error": str(exc)},
        )

    # Log configuration
    logger.info(
        "Application configured",
        extra={
            "debug": settings.debug,
            "cors_origins": settings.cors_origins_list,
            "feature_screen_source": settings.feature_screen_source,
        },
    )

    yield

    # Cleanup
    try:
        from app.core.database import close_database

        await close_database()
    except Exception as exc:  # noqa: BLE001 - shutdown must not raise
        logger.warning("Error closing database", extra={"error": str(exc)})
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
        allow_origins=settings.cors_origins_list,
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
        # Starlette's error middleware sits outside CORSMiddleware, so a 500
        # would otherwise reach the browser without CORS headers and be
        # misreported as a CORS failure. Echo the allowed origin explicitly.
        headers = {}
        origin = request.headers.get("origin")
        if origin and origin in settings.cors_origins_list:
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Vary": "Origin",
            }
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "type": "internal_error"},
            headers=headers,
        )

    # Include routers
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(problems_router, prefix="/api/v1", tags=["problems", "execution"])
    app.include_router(hints_router, prefix="/api/v1", tags=["mentor"])
    app.include_router(history_router, prefix="/api/v1", tags=["history"])
    app.include_router(progress_router, prefix="/api/v1", tags=["progress"])
    app.include_router(capture_router, prefix="/api/v1", tags=["capture"])

    # WebSocket endpoint for real-time code analysis
    @app.websocket("/ws/code-analysis")
    async def websocket_code_analysis(websocket: WebSocket, session_token: str | None = None):
        await websocket_endpoint(websocket, session_token or "anonymous")

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    # Bind to loopback by default: this is a single-user local app (Q5).
    # Pass --host explicitly when a LAN address is genuinely needed.
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use our custom logging setup
    )
