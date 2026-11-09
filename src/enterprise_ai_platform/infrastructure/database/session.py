"""
SQLAlchemy async session factory and dependency injection provider.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from enterprise_ai_platform.infrastructure.database.connection_manager import (
    get_async_engine,
)

_session_factory: async_sessionmaker[AsyncSession] | None = None


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
