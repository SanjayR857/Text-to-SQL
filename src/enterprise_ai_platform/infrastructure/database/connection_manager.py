"""
Database connection pool manager.

Initialises, configures, checks health, and disposes the SQLAlchemy AsyncEngine.
"""
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from enterprise_ai_platform.core.config import get_settings

_async_engine: AsyncEngine | None = None


def get_async_engine() -> AsyncEngine:
    """
    Retrieve or lazily initialize the singleton SQLAlchemy AsyncEngine.

    Configured with connection pool limits, pool_pre_ping to detect stale
    or dropped connections, and timeouts derived from application settings.
    """
    global _async_engine
    if _async_engine is None:
        settings = get_settings()
        _async_engine = create_async_engine(
            url=settings.database_url.get_secret_value(),
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_pre_ping=True,
            echo=settings.debug,
        )
    return _async_engine


async def close_engine() -> None:
    """
    Gracefully dispose all connection pools in the AsyncEngine during application shutdown.
    """
    global _async_engine
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None


async def check_connection() -> dict[str, Any]:
    """
    Verify database reachability and return pool metrics for health checks.
    """
    engine = get_async_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        result.scalar_one()

    pool = engine.pool
    return {
        "status": "healthy",
        "pool_size": pool.size(),
        "checked_in_connections": pool.checkedin(),
        "checked_out_connections": pool.checkedout(),
        "overflow": pool.overflow(),
    }
