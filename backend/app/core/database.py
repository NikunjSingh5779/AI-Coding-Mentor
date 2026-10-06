"""SQLAlchemy 2.x database lifecycle and dependency helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.session import Base


settings = get_settings()

engine_kwargs: dict[str, object] = {
    "echo": settings.debug,
    "pool_pre_ping": True,
}
if settings.database_url.startswith("sqlite+aiosqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database() -> None:
    """Create application tables for local/dev use.

    Production can replace this with Alembic migrations without changing the
    application-facing session dependency.
    """

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Dispose all database connections."""

    await engine.dispose()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that owns one transaction-scoped session."""

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


__all__ = ["AsyncSessionLocal", "Base", "close_database", "engine", "get_db_session", "init_database"]
