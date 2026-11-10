"""
Unit tests for RBAC domain rules, vertical isolation, and authorization guards.
"""
from uuid import UUID, uuid4
import pytest
from fastapi import HTTPException, status

from enterprise_ai_platform.api.dependencies import (
    require_ca_admin,
    require_vertical_access,
)
from enterprise_ai_platform.auth.role import Area, Role
from enterprise_ai_platform.auth.user import (
    AccessScope,
    RoleAssignmentContext,
    UserContext,
)


@pytest.fixture
def ca_admin_user() -> UserContext:
    """Fixture for a Central Application Administrator."""
    return UserContext(
        user_id=uuid4(),
        email="admin@company.com",
        assignments=[
            RoleAssignmentContext(
                role=Role.ADMIN,
                vertical_code="CHAIO",
                vertical_name="Central AI Office",
                vertical_area=Area.CentralApplication,
            )
        ],
        access_scope=AccessScope(vertical_codes=["CHAIO"], project_ids=[]),
    )


@pytest.fixture
def multi_role_user() -> UserContext:
    """
    Fixture for Alice:
      - CHIEF in CHAIO (Central AI Office)
      - CON (Consultant) in CHDLO (Delivery Office)
    """
    return UserContext(
        user_id=uuid4(),
        email="alice@company.com",
        assignments=[
            RoleAssignmentContext(
                role=Role.CHIEF,
                vertical_code="CHAIO",
                vertical_name="Central AI Office",
                vertical_area=Area.IndividualModule,
            ),
            RoleAssignmentContext(
                role=Role.CON,
                vertical_code="CHDLO",
                vertical_name="Delivery Office",
                vertical_area=Area.IndividualModule,
            ),
        ],
        access_scope=AccessScope(vertical_codes=["CHAIO", "CHDLO"], project_ids=[]),
    )


@pytest.fixture
def unassigned_employee() -> UserContext:
    """Fixture for an authenticated employee with no elevated vertical roles."""
    return UserContext(
        user_id=uuid4(),
        email="bob.employee@company.com",
        assignments=[],
        access_scope=AccessScope(vertical_codes=[], project_ids=[]),
    )


# ---------------------------------------------------------------------------
# 1. Multi-Role Scoping & Cross-Vertical Isolation
# ---------------------------------------------------------------------------


def test_cross_vertical_isolation(multi_role_user: UserContext):
    """Verify that a role in Vertical A does not leak into Vertical B."""
    # Alice is CHIEF in CHAIO
    assert multi_role_user.has_role_in_vertical(Role.CHIEF, "CHAIO") is True
    assert multi_role_user.has_role_in_vertical(Role.CHIEF, "chaio") is True  # Case-insensitive

    # Alice is ONLY a CON in CHDLO, NOT a CHIEF
    assert multi_role_user.has_role_in_vertical(Role.CHIEF, "CHDLO") is False
    assert multi_role_user.has_role_in_vertical(Role.CON, "CHDLO") is True

    # Alice has no role in an unrelated vertical
    assert multi_role_user.has_role_in_vertical(Role.CHIEF, "CHFIN") is False
    assert multi_role_user.has_role_in_vertical(Role.CON, "CHFIN") is False


def test_get_roles_for_vertical(multi_role_user: UserContext):
    """Verify retrieving list of roles for specific verticals."""
    assert multi_role_user.get_roles_for_vertical("CHAIO") == [Role.CHIEF]
    assert multi_role_user.get_roles_for_vertical("chdlo") == [Role.CON]
    assert multi_role_user.get_roles_for_vertical("UNKNOWN") == []


def test_empty_or_whitespace_vertical_code_rejected(multi_role_user: UserContext):
    """Verify defensive handling of empty or blank vertical inputs."""
    assert multi_role_user.has_role_in_vertical(Role.CHIEF, "") is False
    assert multi_role_user.has_role_in_vertical(Role.CHIEF, "   ") is False
    assert multi_role_user.has_vertical("") is False
    assert multi_role_user.has_vertical("   ") is False
    assert multi_role_user.get_roles_for_vertical("") == []
    assert multi_role_user.get_roles_for_vertical("   ") == []


# ---------------------------------------------------------------------------
# 2. Central Application Admin Logic
# ---------------------------------------------------------------------------


def test_ca_admin_identification(ca_admin_user: UserContext, multi_role_user: UserContext):
    """Verify CA Admin requires both ADMIN role AND CentralApplication area."""
    assert ca_admin_user.is_ca_admin is True
    assert multi_role_user.is_ca_admin is False

    # ADMIN in an IndividualModule is NOT a CA Admin
    module_admin = UserContext(
        user_id=uuid4(),
        email="module.admin@company.com",
        assignments=[
            RoleAssignmentContext(
                role=Role.ADMIN,
                vertical_code="CHFIN",
                vertical_name="Finance Office",
                vertical_area=Area.IndividualModule,
            )
        ],
    )
    assert module_admin.is_ca_admin is False


# ---------------------------------------------------------------------------
# 3. Unassigned Employee Handling
# ---------------------------------------------------------------------------


def test_unassigned_employee_state(
    unassigned_employee: UserContext, multi_role_user: UserContext
):
    """Verify that unassigned employees are correctly flagged and hold no roles."""
    assert unassigned_employee.is_unassigned_employee is True
    assert unassigned_employee.assignments == []
    assert unassigned_employee.has_role(Role.ADMIN) is False
    assert unassigned_employee.has_role_in_vertical(Role.CON, "CHAIO") is False
    assert unassigned_employee.has_vertical("CHAIO") is False

    assert multi_role_user.is_unassigned_employee is False


# ---------------------------------------------------------------------------
# 4. Route Guard Dependencies
# ---------------------------------------------------------------------------


def test_require_ca_admin_guard(ca_admin_user: UserContext, multi_role_user: UserContext):
    """Verify require_ca_admin dependency allows CA Admin and rejects others with 403."""
    # CA Admin passes
    result = require_ca_admin(ca_admin_user)
    assert result == ca_admin_user

    # Non-admin raises 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        require_ca_admin(multi_role_user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Central Application Administrator access required" in exc_info.value.detail


def test_require_vertical_access_guard_enforces_roles(
    ca_admin_user: UserContext, multi_role_user: UserContext
):
    """Verify require_vertical_access dependency enforces vertical boundaries."""
    chief_guard = require_vertical_access(Role.CHIEF)

    # 1. CA Admin bypasses vertical-specific restriction
    assert chief_guard(vertical_code="CHDLO", context=ca_admin_user) == ca_admin_user

    # 2. Alice is CHIEF in CHAIO -> passes
    assert chief_guard(vertical_code="CHAIO", context=multi_role_user) == multi_role_user

    # 3. Alice is NOT CHIEF in CHDLO (only CON) -> 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        chief_guard(vertical_code="CHDLO", context=multi_role_user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Role 'CHIEF' required in vertical 'CHDLO'" in exc_info.value.detail

    # 4. General vertical access without specific role
    any_access_guard = require_vertical_access(None)
    assert any_access_guard(vertical_code="CHDLO", context=multi_role_user) == multi_role_user
    with pytest.raises(HTTPException) as exc_info:
        any_access_guard(vertical_code="CHFIN", context=multi_role_user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
