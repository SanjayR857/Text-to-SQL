"""
Unit tests for RequestLoggingMiddleware.
"""
from uuid import UUID
from unittest.mock import patch

from fastapi import FastAPI, Request
import httpx
import pytest

from enterprise_ai_platform.api.middleware.logging import RequestLoggingMiddleware
from enterprise_ai_platform.auth.user import RequestIdentity, UserContext


@pytest.fixture
def logging_app() -> FastAPI:
    """Create test application wrapped with RequestLoggingMiddleware."""
    app = FastAPI(title="Logging Test App")
    app.add_middleware(RequestLoggingMiddleware, excluded_paths=("/api/v1/health",))

    @app.get("/api/v1/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/data")
    async def get_data():
        return {"data": "test"}

    @app.get("/api/v1/authenticated")
    async def auth_endpoint(request: Request):
        # Simulate authenticated state
        request.state.identity = RequestIdentity(email="sanjayr9586@gmail.com", auth_method="dev_header")
        request.state.user_context = UserContext(
            user_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            email="sanjayr9586@gmail.com",
        )
        return {"status": "authenticated"}

    @app.get("/api/v1/error")
    async def error_endpoint():
        raise RuntimeError("Simulated crash")

    return app


@pytest.mark.asyncio
async def test_health_endpoint_excluded_from_logging(logging_app: FastAPI):
    """Verify that requests to excluded endpoints do not emit an access log."""
    with patch("enterprise_ai_platform.api.middleware.logging.logger.info") as mock_info:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=logging_app),
            base_url="http://testserver",
        ) as client:
            res = await client.get("/api/v1/health")
            assert res.status_code == 200
            mock_info.assert_not_called()


@pytest.mark.asyncio
async def test_normal_request_logs_metadata_and_duration(logging_app: FastAPI):
    """Verify normal requests log method, path, status_code, and duration_ms."""
    with patch("enterprise_ai_platform.api.middleware.logging.logger.info") as mock_info:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=logging_app),
            base_url="http://testserver",
        ) as client:
            res = await client.get("/api/v1/data")
            assert res.status_code == 200
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            assert args[0] == "http_request_finished"
            assert kwargs["method"] == "GET"
            assert kwargs["path"] == "/api/v1/data"
            assert kwargs["status_code"] == 200
            assert "duration_ms" in kwargs
            assert kwargs["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_authenticated_request_logs_user_id(logging_app: FastAPI):
    """Verify authenticated requests log user_id from downstream request state."""
    with patch("enterprise_ai_platform.api.middleware.logging.logger.info") as mock_info:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=logging_app),
            base_url="http://testserver",
        ) as client:
            res = await client.get("/api/v1/authenticated")
            assert res.status_code == 200
            mock_info.assert_called_once()
            _, kwargs = mock_info.call_args
            assert kwargs["user_id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.mark.asyncio
async def test_unhandled_exception_logs_failure(logging_app: FastAPI):
    """Verify exceptions in request handling log failure with status 500 and duration."""
    with patch("enterprise_ai_platform.api.middleware.logging.logger.exception") as mock_exception:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=logging_app, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            res = await client.get("/api/v1/error")
            assert res.status_code == 500
            mock_exception.assert_called_once()
            args, kwargs = mock_exception.call_args
            assert args[0] == "http_request_failed"
            assert kwargs["status_code"] == 500
            assert kwargs["path"] == "/api/v1/error"
            assert "duration_ms" in kwargs
