"""
Unit tests for RequestIdMiddleware and correlation ID propagation.
"""
import asyncio
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
import httpx
import pytest
import structlog

from enterprise_ai_platform.api.middleware.request_id import (
    REQUEST_ID_HEADER,
    RequestIdMiddleware,
    validate_or_generate_request_id,
)


@pytest.fixture
def request_id_app() -> FastAPI:
    """Create test application wrapped with pure ASGI RequestIdMiddleware."""
    app = FastAPI(title="RequestId Test App")
    app.add_middleware(RequestIdMiddleware)

    @app.get("/test-id")
    async def get_id(request: Request):
        req_id = getattr(request.state, "request_id", None)
        # Verify that structlog contextvar is properly bound during request execution
        ctx = structlog.contextvars.get_contextvars()
        return {
            "state_request_id": req_id,
            "structlog_request_id": ctx.get("request_id"),
        }

    return app


@pytest.mark.asyncio
async def test_request_without_id_generates_uuid(request_id_app: FastAPI):
    """Verify that requests missing X-Request-ID receive a newly generated UUID."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=request_id_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/test-id")
        assert response.status_code == 200
        header_id = response.headers.get(REQUEST_ID_HEADER)
        assert header_id is not None
        # Must be valid UUID
        parsed_uuid = UUID(header_id)
        assert str(parsed_uuid) == header_id

        data = response.json()
        assert data["state_request_id"] == header_id
        assert data["structlog_request_id"] == header_id


@pytest.mark.asyncio
async def test_request_with_valid_id_is_preserved(request_id_app: FastAPI):
    """Verify that a valid incoming UUID X-Request-ID is preserved."""
    test_uuid = str(uuid4())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=request_id_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/test-id", headers={REQUEST_ID_HEADER: test_uuid})
        assert response.status_code == 200
        assert response.headers.get(REQUEST_ID_HEADER) == test_uuid
        data = response.json()
        assert data["state_request_id"] == test_uuid
        assert data["structlog_request_id"] == test_uuid


@pytest.mark.asyncio
async def test_request_with_malformed_id_generates_new_uuid(request_id_app: FastAPI):
    """Verify that an invalid or malicious incoming ID is rejected and replaced with a valid UUID."""
    malformed_id = "malformed-id-or-sql-injection-attempt-';--"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=request_id_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/test-id", headers={REQUEST_ID_HEADER: malformed_id})
        assert response.status_code == 200
        header_id = response.headers.get(REQUEST_ID_HEADER)
        assert header_id is not None
        assert header_id != malformed_id
        # Must be replaced with a valid UUID
        parsed = UUID(header_id)
        assert str(parsed) == header_id


@pytest.mark.asyncio
async def test_contextvars_cleaned_up_after_request(request_id_app: FastAPI):
    """Verify that structlog context is cleaned up after request processing."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=request_id_app),
        base_url="http://testserver",
    ) as client:
        await client.get("/test-id")
        # Outside of the request lifecycle, contextvars must be clean
        ctx = structlog.contextvars.get_contextvars()
        assert "request_id" not in ctx


@pytest.mark.asyncio
async def test_concurrent_requests_do_not_leak_request_ids(request_id_app: FastAPI):
    """Verify that concurrent requests maintain isolated request IDs."""
    id1 = str(uuid4())
    id2 = str(uuid4())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=request_id_app),
        base_url="http://testserver",
    ) as client:
        res1, res2 = await asyncio.gather(
            client.get("/test-id", headers={REQUEST_ID_HEADER: id1}),
            client.get("/test-id", headers={REQUEST_ID_HEADER: id2}),
        )
        assert res1.headers.get(REQUEST_ID_HEADER) == id1
        assert res1.json()["state_request_id"] == id1
        assert res2.headers.get(REQUEST_ID_HEADER) == id2
        assert res2.json()["state_request_id"] == id2
