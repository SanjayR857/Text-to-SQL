"""
Unit tests for AuthorizedSchemaService.
"""
from uuid import uuid4
import pytest

from auth import PolicyResolver
from text_to_sql import (
    AuthorizedSchemaService,
)
from auth.role import Area, Role
from auth.user import (
    AccessScope as UserAccessScope,
    RoleAssignmentContext,
    UserContext,
)


@pytest.fixture
def unassigned_employee_user() -> UserContext:
    """Fixture for regular employee with SELF-scope."""
    return UserContext(
        user_id=uuid4(),
        email="john.doe@company.com",
        assignments=[],
        access_scope=UserAccessScope(vertical_codes=[], project_ids=[]),
    )


@pytest.fixture
def ca_admin_user() -> UserContext:
    """Fixture for CA Administrator."""
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
        access_scope=UserAccessScope(vertical_codes=["CHAIO"], project_ids=[]),
    )


class TestAuthorizedSchemaService:
    """Tests verifying schema projection, column filtering, and join hints for LLM prompts."""

    def test_employee_schema_omits_unauthorized_tables_and_columns(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Scoreboard table and confidential compensation columns are omitted from prompt schema."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["EmployeeInformation", "OfficeAttendance", "Scoreboard"],
        )
        service = AuthorizedSchemaService()

        # 1. Check catalog
        catalog = service.get_authorized_table_catalog(ctx)
        assert "EmployeeInformation" in catalog
        assert "OfficeAttendance" in catalog
        assert "Scoreboard" not in catalog  # Completely omitted

        # Check column filtering on EmployeeInformation
        emp_cols = catalog["EmployeeInformation"]
        assert "employeeName" in emp_cols
        assert "employeeMailId" in emp_cols
        assert "fixedCtc" not in emp_cols  # Omitted
        assert "variableCtc" not in emp_cols  # Omitted
        assert "currentCtc" not in emp_cols  # Omitted
        assert "panNumber" not in emp_cols  # Omitted

        # 2. Check generated prompt text
        prompt_text = service.build_prompt_schema(ctx)
        assert "#### Table: `EmployeeInformation`" in prompt_text
        assert "#### Table: `OfficeAttendance`" in prompt_text
        assert "Scoreboard" not in prompt_text
        assert "fixedCtc" not in prompt_text

        # Verify join hints for mutually accessible tables
        assert (
            "EmployeeInformation.employeeMailId = OfficeAttendance.employeeMailId"
            in prompt_text
        )

    def test_admin_schema_includes_scoreboard_and_compensation(
        self, ca_admin_user: UserContext
    ) -> None:
        """CA Admin schema includes Scoreboard and compensation columns."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            ca_admin_user,
            requested_tables=["EmployeeInformation", "Scoreboard"],
        )
        service = AuthorizedSchemaService()

        catalog = service.get_authorized_table_catalog(ctx)
        assert "Scoreboard" in catalog
        assert "EmployeeInformation" in catalog

        emp_cols = catalog["EmployeeInformation"]
        assert "fixedCtc" in emp_cols
        assert "currentCtc" in emp_cols

        prompt_text = service.build_prompt_schema(ctx)
        assert "#### Table: `Scoreboard`" in prompt_text
        assert "- `fixedCtc`" in prompt_text

    def test_target_tables_filtering(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Passing target_tables restricts prompt output to only requested accessible tables."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["EmployeeInformation", "OfficeAttendance"],
        )
        service = AuthorizedSchemaService()

        prompt_text = service.build_prompt_schema(
            ctx, target_tables=["EmployeeInformation"]
        )

        assert "#### Table: `EmployeeInformation`" in prompt_text
        assert "OfficeAttendance" not in prompt_text

    def test_inaccessible_target_table_handled_gracefully(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Requesting inaccessible target tables produces a graceful warning."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["Scoreboard"],
        )
        service = AuthorizedSchemaService()

        prompt_text = service.build_prompt_schema(
            ctx, target_tables=["Scoreboard"]
        )

        assert "No accessible tables available" in prompt_text
