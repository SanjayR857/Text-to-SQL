"""
Unit tests for SecurityHeadersMiddleware.
"""
from fastapi import FastAPI
import httpx
import pytest

from api.middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def dev_security_app() -> FastAPI:
    """Create test application wrapped with SecurityHeadersMiddleware in development mode."""
    app = FastAPI(title="Security Headers Dev App")
    app.add_middleware(SecurityHeadersMiddleware, is_production=False)

    @app.get("/test")
    async def endpoint():
        return {"ok": True}

    return app


@pytest.fixture
def prod_security_app() -> FastAPI:
    """Create test application wrapped with SecurityHeadersMiddleware in production mode."""
    app = FastAPI(title="Security Headers Prod App")
    app.add_middleware(SecurityHeadersMiddleware, is_production=True)

    @app.get("/test")
    async def endpoint():
        return {"ok": True}

    return app


@pytest.mark.asyncio
async def test_standard_security_headers_present(dev_security_app: FastAPI):
    """Verify that OWASP recommended baseline security headers are injected."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=dev_security_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/test")
        assert response.status_code == 200
        headers = response.headers
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "default-src 'self'" in headers.get("content-security-policy", "")
        assert "camera=()" in headers.get("permissions-policy", "")
        # In development, HSTS must NOT be set
        assert "strict-transport-security" not in headers


@pytest.mark.asyncio
async def test_hsts_applied_in_production(prod_security_app: FastAPI):
    """Verify that Strict-Transport-Security is applied when in production mode."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=prod_security_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/test")
        assert response.status_code == 200
        hsts = response.headers.get("strict-transport-security")
        assert hsts is not None
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
