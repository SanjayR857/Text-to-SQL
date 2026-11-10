"""
Unit and integration tests for AuthenticationMiddleware and development identity resolution.
"""
from fastapi import Depends, FastAPI, Request, status
import httpx
from pydantic import ValidationError
import pytest

from enterprise_ai_platform.api.dependencies import get_current_identity
from enterprise_ai_platform.api.middleware.authentication import (
    DEV_USER_EMAIL_HEADER,
    AuthenticationMiddleware,
)
from enterprise_ai_platform.core.config import Settings
from enterprise_ai_platform.domain.identity.user import RequestIdentity


def create_test_app(settings: Settings) -> FastAPI:
    """Helper to construct a test FastAPI app with AuthenticationMiddleware and test routes."""
    app = FastAPI(title="Auth Middleware Test App")
    app.add_middleware(AuthenticationMiddleware, settings=settings)

    @app.get("/api/v1/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/api/v1/protected")
    async def protected_endpoint(request: Request):
        identity: RequestIdentity = request.state.identity
        return {
            "email": identity.email,
            "auth_method": identity.auth_method,
            "state_user_email": getattr(request.state, "user_email", None),
        }

    @app.get("/api/v1/identity-via-dep")
    async def dependency_endpoint(identity: RequestIdentity = Depends(get_current_identity)):
        return {
            "email": identity.email,
            "auth_method": identity.auth_method,
        }

    return app


# -----------------------------------------------------------------------------
# 1. Configuration Safety Tests
# -----------------------------------------------------------------------------

def test_settings_default_allow_dev_auth_is_false():
    """Verify that allow_dev_auth defaults to False."""
    settings = Settings(
        database_url="postgresql+asyncpg://mock:mock@localhost:5432/mock",
        checkpoint_database_url="postgresql+asyncpg://mock:mock@localhost:5432/mock",
        azure_openai_endpoint="https://mock.openai.azure.com/",
        azure_openai_chat_deployment="gpt-4o",
        azure_openai_embedding_deployment="text-embedding-3-large",
        entra_tenant_id="00000000-0000-0000-0000-000000000000",
        entra_api_audience="api://mock",
    )
    assert settings.allow_dev_auth is False


def test_settings_cannot_enable_dev_auth_in_production():
    """Verify that enabling allow_dev_auth in production raises a validation error."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            environment="production",
            allow_dev_auth=True,
            database_url="postgresql+asyncpg://mock:mock@localhost:5432/mock",
            checkpoint_database_url="postgresql+asyncpg://mock:mock@localhost:5432/mock",
            azure_openai_endpoint="https://mock.openai.azure.com/",
            azure_openai_chat_deployment="gpt-4o",
            azure_openai_embedding_deployment="text-embedding-3-large",
            entra_tenant_id="00000000-0000-0000-0000-000000000000",
            entra_api_audience="api://mock",
        )
    assert "ALLOW_DEV_AUTH must not be enabled in production" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 2. Authentication Middleware Tests
# -----------------------------------------------------------------------------

@pytest.fixture
def dev_settings() -> Settings:
    """Settings instance with development authentication enabled."""
    return Settings(
        environment="development",
        allow_dev_auth=True,
        database_url="postgresql+asyncpg://mock:mock@localhost:5432/mock",
        checkpoint_database_url="postgresql+asyncpg://mock:mock@localhost:5432/mock",
        azure_openai_endpoint="https://mock.openai.azure.com/",
        azure_openai_chat_deployment="gpt-4o",
        azure_openai_embedding_deployment="text-embedding-3-large",
        entra_tenant_id="00000000-0000-0000-0000-000000000000",
        entra_api_audience="api://mock",
    )


@pytest.fixture
def disabled_dev_settings() -> Settings:
    """Settings instance with development authentication disabled."""
    return Settings(
        environment="development",
        allow_dev_auth=False,
        database_url="postgresql+asyncpg://mock:mock@localhost:5432/mock",
        checkpoint_database_url="postgresql+asyncpg://mock:mock@localhost:5432/mock",
        azure_openai_endpoint="https://mock.openai.azure.com/",
        azure_openai_chat_deployment="gpt-4o",
        azure_openai_embedding_deployment="text-embedding-3-large",
        entra_tenant_id="00000000-0000-0000-0000-000000000000",
        entra_api_audience="api://mock",
    )


@pytest.mark.asyncio
async def test_auth_success_with_dev_header(dev_settings: Settings):
    """Test valid identity header extracts and normalizes email and attaches to state."""
    app = create_test_app(dev_settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/protected",
            headers={DEV_USER_EMAIL_HEADER: "  SanjayR9586@Gmail.Com  "},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "sanjayr9586@gmail.com"
        assert data["auth_method"] == "dev_header"
        assert data["state_user_email"] == "sanjayr9586@gmail.com"


@pytest.mark.asyncio
async def test_auth_success_via_fastapi_dependency(dev_settings: Settings):
    """Test get_current_identity dependency retrieves the resolved identity."""
    app = create_test_app(dev_settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/identity-via-dep",
            headers={DEV_USER_EMAIL_HEADER: "elena.rostova.ai@gmail.com"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "elena.rostova.ai@gmail.com"
        assert data["auth_method"] == "dev_header"


@pytest.mark.asyncio
async def test_auth_missing_identity_header(dev_settings: Settings):
    """Test missing identity header on protected route returns 401."""
    app = create_test_app(dev_settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/protected")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": "Authentication required: missing identity header."
        }


@pytest.mark.asyncio
async def test_auth_disabled_returns_403(disabled_dev_settings: Settings):
    """Test that when allow_dev_auth=False, request is rejected with 403 Forbidden."""
    app = create_test_app(disabled_dev_settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/protected",
            headers={DEV_USER_EMAIL_HEADER: "sanjayr9586@gmail.com"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {
            "detail": "Development authentication is disabled."
        }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_email",
    [
        "",
        "   ",
        "not-an-email",
        "user@",
        "@company.com",
        "user@company",
        "user space@company.com",
    ],
)
async def test_auth_invalid_email_format_returns_401(dev_settings: Settings, invalid_email: str):
    """Test malformed email formats are rejected with 401 Unauthorized."""
    app = create_test_app(dev_settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/protected",
            headers={DEV_USER_EMAIL_HEADER: invalid_email},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json() == {
            "detail": "Invalid identity email format."
        }


@pytest.mark.asyncio
async def test_public_endpoint_bypasses_authentication(disabled_dev_settings: Settings):
    """Test that exempt paths like /api/v1/health proceed without identity headers."""
    app = create_test_app(disabled_dev_settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}
