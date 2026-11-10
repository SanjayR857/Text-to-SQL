"""
Unit tests for UserContextService and business logic resolution.
"""
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from enterprise_ai_platform.application.authorization.user_context_service import (
    UserContextService,
)
from enterprise_ai_platform.core.exceptions import (
    DatabaseUnavailableError,
    InvalidIdentityError,
    NoActiveAssignmentsError,
    UserNotFoundError,
)
from enterprise_ai_platform.domain.identity.role import Area, Role
from enterprise_ai_platform.infrastructure.database.repositories.user_context_repository import (
    UserContextRepository,
)


@pytest.fixture
def mock_repo() -> AsyncMock:
    """Fixture providing a mock UserContextRepository."""
    return AsyncMock(spec=UserContextRepository)


@pytest.fixture
def service(mock_repo: AsyncMock) -> UserContextService:
    """Fixture providing UserContextService with mocked repository."""
    return UserContextService(mock_repo)


@pytest.mark.asyncio
async def test_lead_user_context_resolution(service: UserContextService, mock_repo: AsyncMock):
    """Test that a LEAD role user gets assigned project IDs populated."""
    user_uuid = UUID("11111111-1111-1111-1111-111111111111")
    mock_repo.get_user_id_by_email.return_value = user_uuid
    mock_repo.get_active_role_assignments.return_value = [
        {
            "role": "LEAD",
            "vertical_code": "CHAIO",
            "vertical_name": "Chief AI Office",
            "vertical_area": "IndividualModule",
        }
    ]
    mock_repo.get_assigned_lead_project_ids.return_value = ["proj_alpha_ai_001"]

    ctx = await service.resolve_user_context("Lead.User@Enterprise.AI")

    assert ctx.user_id == user_uuid
    assert ctx.email == "lead.user@enterprise.ai"
    assert len(ctx.assignments) == 1
    assert ctx.assignments[0].role == Role.LEAD
    assert ctx.assignments[0].vertical_code == "CHAIO"
    assert ctx.assignments[0].vertical_area == Area.IndividualModule
    assert ctx.access_scope.vertical_codes == ["CHAIO"]
    assert ctx.access_scope.project_ids == ["proj_alpha_ai_001"]
    mock_repo.get_assigned_lead_project_ids.assert_awaited_once_with("lead.user@enterprise.ai")


@pytest.mark.asyncio
async def test_chief_user_context_resolution(service: UserContextService, mock_repo: AsyncMock):
    """Test that a CHIEF role user gets vertical codes but empty project_ids."""
    user_uuid = UUID("22222222-2222-2222-2222-222222222222")
    mock_repo.get_user_id_by_email.return_value = user_uuid
    mock_repo.get_active_role_assignments.return_value = [
        {
            "role": "CHIEF",
            "vertical_code": "CHAIO",
            "vertical_name": "Chief AI Office",
            "vertical_area": "IndividualModule",
        }
    ]

    ctx = await service.resolve_user_context("chief@enterprise.ai")

    assert ctx.user_id == user_uuid
    assert ctx.email == "chief@enterprise.ai"
    assert len(ctx.assignments) == 1
    assert ctx.assignments[0].role == Role.CHIEF
    assert ctx.access_scope.vertical_codes == ["CHAIO"]
    assert ctx.access_scope.project_ids == []
    # Project retrieval must NOT be queried for non-LEAD users
    mock_repo.get_assigned_lead_project_ids.assert_not_called()


@pytest.mark.asyncio
async def test_multi_role_user_context_resolution(service: UserContextService, mock_repo: AsyncMock):
    """Test multi-role user with CHIEF in one vertical and LEAD in another."""
    user_uuid = UUID("33333333-3333-3333-3333-333333333333")
    mock_repo.get_user_id_by_email.return_value = user_uuid
    mock_repo.get_active_role_assignments.return_value = [
        {
            "role": "CHIEF",
            "vertical_code": "CHTAO",
            "vertical_name": "Chief Talent Office",
            "vertical_area": "IndividualModule",
        },
        {
            "role": "LEAD",
            "vertical_code": "CHDLO",
            "vertical_name": "Chief Delivery Office",
            "vertical_area": "IndividualModule",
        },
    ]
    mock_repo.get_assigned_lead_project_ids.return_value = ["proj_101", "proj_102"]

    ctx = await service.resolve_user_context("leader@enterprise.ai")

    assert ctx.user_id == user_uuid
    assert len(ctx.assignments) == 2
    assert ctx.access_scope.vertical_codes == ["CHDLO", "CHTAO"]
    assert ctx.access_scope.project_ids == ["proj_101", "proj_102"]
    mock_repo.get_assigned_lead_project_ids.assert_awaited_once_with("leader@enterprise.ai")


@pytest.mark.asyncio
async def test_unknown_user_raises_404(service: UserContextService, mock_repo: AsyncMock):
    """Test unknown user email raises UserNotFoundError."""
    mock_repo.get_user_id_by_email.return_value = None

    with pytest.raises(UserNotFoundError) as exc_info:
        await service.resolve_user_context("unknown@enterprise.ai")
    assert "does not exist" in str(exc_info.value)


@pytest.mark.asyncio
async def test_no_active_assignments_raises_403(service: UserContextService, mock_repo: AsyncMock):
    """Test user with no active assignments raises NoActiveAssignmentsError."""
    mock_repo.get_user_id_by_email.return_value = UUID("44444444-4444-4444-4444-444444444444")
    mock_repo.get_active_role_assignments.return_value = []

    with pytest.raises(NoActiveAssignmentsError) as exc_info:
        await service.resolve_user_context("inactive@enterprise.ai")
    assert "no active vertical role assignments" in str(exc_info.value)


@pytest.mark.asyncio
async def test_database_error_propagates(service: UserContextService, mock_repo: AsyncMock):
    """Test that repository database errors propagate as DatabaseUnavailableError."""
    mock_repo.get_user_id_by_email.side_effect = DatabaseUnavailableError("DB connection failed")

    with pytest.raises(DatabaseUnavailableError):
        await service.resolve_user_context("user@enterprise.ai")


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_email", ["", "   ", "not-email", "@no-user.com", "user@"])
async def test_invalid_email_format(service: UserContextService, invalid_email: str):
    """Test malformed email format raises InvalidIdentityError."""
    with pytest.raises(InvalidIdentityError):
        await service.resolve_user_context(invalid_email)
