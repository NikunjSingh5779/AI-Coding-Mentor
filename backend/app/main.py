"""AI Coding Mentor FastAPI composition root."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.analytics import router as analytics_router
from app.api.execution import router as execution_router
from app.api.health import router as health_router
from app.api.mentor import router as mentor_router
from app.api.problems import router as problems_router
from app.api.screen import router as screen_router
from app.api.sessions import router as sessions_router
from app.config import get_settings
from app.core.database import close_database, get_db_session, init_database
from app.core.errors import AppError
from app.core.events import EventBus
from app.core.logging import get_logger, setup_logging
from app.persistence.service import seed_problems
from app.problems.problem_bank import list_all_problems
from app.ws.endpoint import websocket_endpoint


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    await init_database()

    # Seed built-in problems without storing reference solutions in API responses.
    async with app.state.db_session_factory() as db:
        await seed_problems(db, list_all_problems())
        await db.commit()

    app.state.event_bus = EventBus()
    logger.info(
        "AI Coding Mentor started",
        extra={
            "debug": settings.debug,
            "screen_source": settings.feature_screen_source,
            "execution_enabled": settings.execution_enabled,
            "llm_enabled": settings.llm_enabled,
        },
    )
    yield
    await close_database()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level, settings.debug)

    app = FastAPI(
        title="AI Coding Mentor",
        description="Real-time coding analysis, sandbox execution and progressive mentoring.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    from app.core.database import AsyncSessionLocal
    app.state.db_session_factory = AsyncSessionLocal

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "type": exc.error_type},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(_, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application exception")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "type": "internal_error"},
        )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")
    app.include_router(problems_router, prefix="/api/v1")
    app.include_router(execution_router, prefix="/api/v1")
    app.include_router(mentor_router, prefix="/api/v1")
    app.include_router(analytics_router, prefix="/api/v1")
    app.include_router(screen_router, prefix="/api/v1")

    @app.websocket("/ws/code-analysis")
    async def code_analysis_socket(
        websocket: WebSocket,
        session_token: str | None = None,
    ) -> None:
        await websocket_endpoint(websocket, session_token)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=get_settings().debug,
    )
