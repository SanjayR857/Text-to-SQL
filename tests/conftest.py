"""
Global pytest fixtures and test configuration for the Chat Module.
"""
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import FastAPI
import httpx
import pytest

from api.dependencies import DEV_USER_ID
from api.exception_handlers import register
from api.routes.conversations import router as conv_router
from api.routes.feedback import router as feedback_router
from core.database import (
    close_engine,
)
from models.user import User
from core.database import (
    async_db_session,
    reset_session_factory,
)

# Secondary test user for ownership isolation testing
OTHER_USER_ID = UUID("00000000-0000-0000-0000-000000000002")

_DB_AVAILABLE: bool | None = None


@pytest.fixture(autouse=True)
async def db_setup():
    """
    Ensure primary and secondary test users exist in the PostgreSQL users table if available,
    and cleanly dispose connection pool after each test to prevent event loop reuse issues.
    """
    global _DB_AVAILABLE
    if _DB_AVAILABLE is not False:
        try:
            async with async_db_session() as session:
                for uid in [DEV_USER_ID, OTHER_USER_ID]:
                    u = await session.get(User, uid)
                    if u is None:
                        session.add(User(id=uid))
                await session.commit()
            _DB_AVAILABLE = True
        except (OSError, Exception):
            # Allow unit tests to run fast when database is not running locally
            _DB_AVAILABLE = False

    yield

    if _DB_AVAILABLE:
        await close_engine()
        reset_session_factory()


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI application instance with chat routes and exception handlers."""
    test_app = FastAPI(title="Chat Module Test Suite")
    register(test_app)
    test_app.include_router(conv_router)
    test_app.include_router(feedback_router)
    return test_app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Provide an authenticated AsyncClient bound to the test app."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-User-ID": str(DEV_USER_ID)},
    ) as ac:
        yield ac
