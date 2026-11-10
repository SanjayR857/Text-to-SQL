"""
SQLAlchemy 2.x Declarative Base, connection pool management, and async session factories.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings

# Explicit naming convention for deterministic Alembic migrations and constraint naming
POSTGRESQL_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "chk_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base class for all application models."""

    metadata = MetaData(naming_convention=POSTGRESQL_NAMING_CONVENTION)


_async_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


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


def reset_session_factory() -> None:
    """Reset the session factory singleton, e.g. during engine recreation or tests."""
    global _session_factory
    _session_factory = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Retrieve or lazily initialize the singleton async_sessionmaker.

    Crucial for StreamingOrchestrator and background tasks, which require
    a session factory to construct isolated, short-lived sessions per database
    operation rather than holding an open connection during streaming.
    """
    global _session_factory
    if _session_factory is None:
        engine = get_async_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that yields a request-scoped AsyncSession for standard REST endpoints.
    Commits automatically on successful request completion, rolls back on exception,
    and closes the session upon exit.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def async_db_session() -> AsyncIterator[AsyncSession]:
    """
    Context manager for short-lived sessions outside of HTTP request lifecycles
    (e.g., background workers, streaming completion writes, reconciliation tasks).
    Commits automatically on successful completion and rolls back on exception.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = [
    "Base",
    "get_async_engine",
    "close_engine",
    "check_connection",
    "get_session_factory",
    "reset_session_factory",
    "get_db_session",
    "async_db_session",
]
