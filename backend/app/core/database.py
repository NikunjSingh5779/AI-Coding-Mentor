"""
Database configuration for AI Real-Time Coding Screener
Following MVC pattern: Core layer handles database setup and connections
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator
import logging

# Base class for all models
Base = declarative_base()

# Global engine and session factory
engine = None
AsyncSessionLocal = None

logger = logging.getLogger(__name__)


async def init_database(database_url: str) -> None:
    """Initialize database engine and session factory"""
    global engine, AsyncSessionLocal

    logger.info(f"Initializing database connection...")

    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        future=True,
        pool_pre_ping=True,
    )

    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def close_database() -> None:
    """Close database connections"""
    global engine

    if engine:
        await engine.dispose()
        logger.info("Database connections closed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()