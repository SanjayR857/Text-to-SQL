"""
Integration tests for User Context resolution and /api/v1/auth/me API endpoint.
Tests full request-response lifecycle with PostgreSQL database.
"""
from fastapi import FastAPI
import httpx
import pytest

from api.middleware.authentication import (
    DEV_USER_EMAIL_HEADER,
    AuthenticationMiddleware,
)
from api.routes.auth import router as auth_router
from core.config import Settings
from core.database import close_engine
from core.database import reset_session_factory


@pytest.fixture
def auth_test_app() -> FastAPI:
    """Create test application mounted with auth router and AuthenticationMiddleware."""
    settings = Settings(
        environment="development",
        allow_dev_auth=True,
        database_url="postgresql+asyncpg://postgres:1234@localhost:5432/vectordb",
        checkpoint_database_url="postgresql+asyncpg://postgres:1234@localhost:5432/vectordb",
        azure_openai_endpoint="https://mock.openai.azure.com/",
        azure_openai_chat_deployment="gpt-4o",
        azure_openai_embedding_deployment="text-embedding-3-large",
        entra_tenant_id="00000000-0000-0000-0000-000000000000",
        entra_api_audience="api://mock",
    )
    app = FastAPI(title="User Context Integration Test App")
    app.add_middleware(AuthenticationMiddleware, settings=settings)

    @app.get("/api/v1/health")
    async def health_check():
        return {"status": "healthy"}

    app.include_router(auth_router, prefix="/api/v1")
    return app


@pytest.fixture(autouse=True)
async def cleanup_db():
    """Ensure engine is cleanly disposed between test runs."""
    yield
    await close_engine()
    reset_session_factory()


@pytest.mark.asyncio
async def test_lead_user_context_endpoint(auth_test_app: FastAPI):
    """
    Test Lead user:
    - User UUID resolved from PostgreSQL users table.
    - LEAD role and CHAIO vertical resolved from RoleAssignment & Vertical.
    - Assigned project proj_alpha_ai_001 resolved from ProjectName.teamLeadMails.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=auth_test_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={DEV_USER_EMAIL_HEADER: "vikram.malhotra.lead@gmail.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "vikram.malhotra.lead@gmail.com"
        assert data["user_id"] == "a1b2c3d4-0001-4000-8000-000000000002"
        assert len(data["assignments"]) == 1
        assert data["assignments"][0]["role"] == "LEAD"
        assert data["assignments"][0]["vertical_code"] == "CHAIO"
        assert data["assignments"][0]["vertical_name"] == "Chief AI Office"
        assert data["access_scope"]["vertical_codes"] == ["CHAIO"]
        assert "proj_alpha_ai_001" in data["access_scope"]["project_ids"]
        assert "proj_health_omnichannel_004" in data["access_scope"]["project_ids"]


@pytest.mark.asyncio
async def test_sanjay_lead_admin_user_context_endpoint(auth_test_app: FastAPI):
    """
    Test Lead + Admin user (Sanjay):
    - User UUID resolved from PostgreSQL users table.
    - Multi-role assignments: ADMIN in CA and LEAD in CHAIO.
    - Access scope spans CA and CHAIO, and all lead projects.
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=auth_test_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={DEV_USER_EMAIL_HEADER: "sanjayr9586@gmail.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "sanjayr9586@gmail.com"
        assert data["user_id"] == "e85c0a56-ceb8-4a4f-b449-f481f4018343"
        assert len(data["assignments"]) == 2
        roles = {a["role"] for a in data["assignments"]}
        assert roles == {"ADMIN", "LEAD"}
        assert set(data["access_scope"]["vertical_codes"]) == {"CA", "CHAIO"}
        assert "proj_alpha_ai_001" in data["access_scope"]["project_ids"]
        assert "proj_fintech_copilot_002" in data["access_scope"]["project_ids"]
        assert "proj_supply_chain_005" in data["access_scope"]["project_ids"]


@pytest.mark.asyncio
async def test_chief_user_context_endpoint(auth_test_app: FastAPI):
    """
    Test Chief user:
    - User UUID resolved from PostgreSQL users table.
    - CHIEF role and CHAIO vertical resolved from RoleAssignment & Vertical.
    - project_ids is empty list (per confirmed business decision).
    """
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=auth_test_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={DEV_USER_EMAIL_HEADER: "elena.rostova.ai@gmail.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "elena.rostova.ai@gmail.com"
        assert data["user_id"] == "1f833c6d-19e3-478d-b0aa-0797beffeb44"
        assert len(data["assignments"]) == 1
        assert data["assignments"][0]["role"] == "CHIEF"
        assert data["assignments"][0]["vertical_code"] == "CHAIO"
        assert data["access_scope"]["vertical_codes"] == ["CHAIO"]
        assert data["access_scope"]["project_ids"] == []


@pytest.mark.asyncio
async def test_unknown_user_returns_404(auth_test_app: FastAPI):
    """Test authenticated email that does not exist in users table returns 404."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=auth_test_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={DEV_USER_EMAIL_HEADER: "nonexistent.user@gmail.com"},
        )
        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]


@pytest.mark.asyncio
async def test_user_without_assignments_returns_403(auth_test_app: FastAPI):
    """Test user who exists in users table but has no active role assignments returns 403."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=auth_test_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={DEV_USER_EMAIL_HEADER: "dev.unassigned@gmail.com"},
        )
        assert response.status_code == 403
        assert "no active vertical role assignments" in response.json()["detail"]


@pytest.mark.asyncio
async def test_missing_identity_header_returns_401(auth_test_app: FastAPI):
    """Test missing header on protected route returns 401."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=auth_test_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required: missing identity header."


@pytest.mark.asyncio
async def test_health_public_endpoint_bypasses_auth(auth_test_app: FastAPI):
    """Test public health check succeeds without authentication headers."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=auth_test_app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
