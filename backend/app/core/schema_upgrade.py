"""Small idempotent compatibility upgrades for existing local databases."""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.core.database import engine


async def upgrade_schema() -> None:
    """Add columns introduced after the initial local MVP schema."""

    async with engine.begin() as connection:
        def migrate(sync_connection) -> None:
            inspector = inspect(sync_connection)
            tables = set(inspector.get_table_names())
            if 'code_analyses' not in tables:
                return
            columns = {column['name'] for column in inspector.get_columns('code_analyses')}
            if 'analysis_time_ms' not in columns:
                sync_connection.execute(text("ALTER TABLE code_analyses ADD COLUMN analysis_time_ms FLOAT"))

        await connection.run_sync(migrate)
