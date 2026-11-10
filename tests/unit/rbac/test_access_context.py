"""
Unit tests for authorization access context, column permissions, and predicate specifications.
"""
from uuid import uuid4
import pytest
from pydantic import ValidationError

from rbac import (
    AccessScope,
    ColumnPermission,
    ColumnSensitivity,
    PredicateOperator,
    PredicateSpec,
    ResolvedAccessContext,
    TablePermission,
)
from core.exceptions import (
    AuthorizationError,
    ColumnAccessDeniedError,
    JoinAccessDeniedError,
    PlatformException,
    SqlSecurityError,
    TableAccessDeniedError,
)
from rbac.role import Area, Role
from rbac.user import (
    AccessScope as UserAccessScope,
    RoleAssignmentContext,
    UserContext,
)


@pytest.fixture
def sample_user_context() -> UserContext:
    """Fixture creating an authenticated employee user context."""
    return UserContext(
        user_id=uuid4(),
        email="emp@company.com",
        assignments=[],
        access_scope=UserAccessScope(vertical_codes=[], project_ids=[]),
    )


class TestPredicateSpec:
    """Unit tests for PredicateSpec and PredicateOperator."""

    def test_for_self_factory(self) -> None:
        """PredicateSpec.for_self creates an EQ predicate bound to caller email."""
        pred = PredicateSpec.for_self()
        assert pred.column == "employeeMailId"
        assert pred.operator == PredicateOperator.EQ
        assert pred.parameter_name == "auth_user_email"
        assert not pred.is_derived_subquery

    def test_for_vertical_factory(self) -> None:
        """PredicateSpec.for_vertical creates an IN predicate bound to vertical codes."""
        pred = PredicateSpec.for_vertical()
        assert pred.column == "verticalCode"
        assert pred.operator == PredicateOperator.IN
        assert pred.parameter_name == "auth_vertical_codes"

    def test_for_project_factory(self) -> None:
        """PredicateSpec.for_project creates an IN predicate bound to project IDs."""
        pred = PredicateSpec.for_project()
        assert pred.column == "projectId"
        assert pred.operator == PredicateOperator.IN
        assert pred.parameter_name == "auth_project_ids"

    def test_deny_factory(self) -> None:
        """PredicateSpec.deny creates an ALWAYS_FALSE predicate."""
        pred = PredicateSpec.deny()
        assert pred.operator == PredicateOperator.ALWAYS_FALSE

    def test_custom_operator_requires_expression(self) -> None:
        """Predicate with CUSTOM operator must provide custom_expression."""
        with pytest.raises(ValidationError, match="custom_expression must be provided"):
            PredicateSpec(
                column="customCol",
                operator=PredicateOperator.CUSTOM,
                parameter_name="param1",
            )

    def test_missing_parameter_name_raises(self) -> None:
        """Predicate with EQ/IN operator must provide non-empty parameter_name."""
        with pytest.raises(ValidationError, match="parameter_name must be non-empty"):
            PredicateSpec(
                column="empId",
                operator=PredicateOperator.EQ,
                parameter_name="",
            )

    def test_immutability(self) -> None:
        """PredicateSpec instances are immutable."""
        pred = PredicateSpec.for_self()
        with pytest.raises(ValidationError):
            pred.column = "otherCol"  # type: ignore[misc]


class TestColumnPermission:
    """Unit tests for ColumnPermission."""

    def test_default_deny(self) -> None:
        """ColumnPermission defaults to denying all operations."""
        perm = ColumnPermission(column_name="salary")
        assert not perm.can_select
        assert not perm.can_filter
        assert not perm.can_join
        assert not perm.can_group
        assert not perm.can_aggregate
        assert perm.sensitivity == ColumnSensitivity.INTERNAL

    def test_granular_operation_permissions(self) -> None:
        """Individual operations can be enabled independently."""
        perm = ColumnPermission(
            column_name="employeeName",
            sensitivity=ColumnSensitivity.PUBLIC,
            can_select=True,
            can_filter=True,
            can_join=True,
            can_group=True,
            can_aggregate=False,
        )
        assert perm.can_select
        assert perm.can_filter
        assert perm.can_join
        assert perm.can_group
        assert not perm.can_aggregate

    def test_immutability(self) -> None:
        """ColumnPermission instances are immutable."""
        perm = ColumnPermission(column_name="status", can_select=True)
        with pytest.raises(ValidationError):
            perm.can_select = False  # type: ignore[misc]


class TestTablePermission:
    """Unit tests for TablePermission."""

    def test_default_deny(self) -> None:
        """TablePermission defaults to inaccessible with NONE scope."""
        tbl = TablePermission(table_name="EmployeeInformation")
        assert not tbl.can_read
        assert tbl.scope == AccessScope.NONE
        assert tbl.allowed_select_columns == set()
        assert tbl.allowed_filter_columns == set()
        assert tbl.allowed_aggregate_columns == set()

    def test_operation_specific_column_sets(self) -> None:
        """Computed properties accurately segregate operations."""
        tbl = TablePermission(
            table_name="EmployeeInformation",
            can_read=True,
            scope=AccessScope.SELF,
            columns={
                "id": ColumnPermission(
                    column_name="id",
                    can_select=True,
                    can_filter=True,
                    can_join=True,
                ),
                "employeename": ColumnPermission(
                    column_name="employeeName",
                    can_select=True,
                    can_filter=True,
                    can_group=True,
                ),
                "fixedctc": ColumnPermission(
                    column_name="fixedCtc",
                    sensitivity=ColumnSensitivity.CONFIDENTIAL,
                    can_select=False,
                    can_filter=False,
                    can_aggregate=False,
                ),
                "performancescore": ColumnPermission(
                    column_name="performanceScore",
                    can_select=True,
                    can_aggregate=True,
                ),
            },
        )

        assert tbl.allowed_select_columns == {"id", "employeename", "performancescore"}
        assert tbl.allowed_filter_columns == {"id", "employeename"}
        assert tbl.allowed_join_columns == {"id"}
        assert tbl.allowed_group_columns == {"employeename"}
        assert tbl.allowed_aggregate_columns == {"performancescore"}

        # fixedCtc is completely excluded from all operations
        assert "fixedctc" not in tbl.allowed_select_columns
        assert "fixedctc" not in tbl.allowed_filter_columns
        assert "fixedctc" not in tbl.allowed_aggregate_columns

    def test_case_insensitive_column_lookup(self) -> None:
        """get_column_permission finds column regardless of case."""
        tbl = TablePermission(
            table_name="EmployeeInformation",
            columns={
                "employeemailid": ColumnPermission(
                    column_name="employeeMailId",
                    can_select=True,
                )
            },
        )
        assert tbl.get_column_permission("employeeMailId") is not None
        assert tbl.get_column_permission("EMPLOYEEMAILID") is not None
        assert tbl.get_column_permission("nonExistent") is None


class TestResolvedAccessContext:
    """Unit tests for ResolvedAccessContext."""

    def test_allowed_tables_property(self, sample_user_context: UserContext) -> None:
        """allowed_tables returns only tables where can_read is True."""
        ctx = ResolvedAccessContext(
            user_context=sample_user_context,
            table_permissions={
                "employeeinformation": TablePermission(
                    table_name="EmployeeInformation",
                    can_read=True,
                    scope=AccessScope.SELF,
                ),
                "clientcontracts": TablePermission(
                    table_name="ClientContracts",
                    can_read=False,
                    scope=AccessScope.NONE,
                ),
            },
            parameters={"auth_user_email": "emp@company.com"},
        )

        assert ctx.allowed_tables == {"employeeinformation"}
        assert ctx.is_table_accessible("EmployeeInformation")
        assert ctx.is_table_accessible("EMPLOYEEINFORMATION")
        assert not ctx.is_table_accessible("ClientContracts")
        assert not ctx.is_table_accessible("UnknownTable")

    def test_get_table_permission_case_insensitive(
        self, sample_user_context: UserContext
    ) -> None:
        """get_table_permission handles mixed case lookups."""
        ctx = ResolvedAccessContext(
            user_context=sample_user_context,
            table_permissions={
                "attendancedaily": TablePermission(
                    table_name="AttendanceDaily",
                    can_read=True,
                    scope=AccessScope.SELF,
                ),
            },
        )
        perm = ctx.get_table_permission("AttendanceDaily")
        assert perm is not None
        assert perm.table_name == "AttendanceDaily"

        perm_lower = ctx.get_table_permission("attendancedaily")
        assert perm_lower is not None

        assert ctx.get_table_permission("NoSuchTable") is None


class TestAuthorizationExceptions:
    """Unit tests verifying domain exception inheritance hierarchy."""

    def test_exception_inheritance(self) -> None:
        """All authorization exceptions must inherit from AuthorizationError and PlatformException."""
        assert issubclass(AuthorizationError, PlatformException)
        assert issubclass(TableAccessDeniedError, AuthorizationError)
        assert issubclass(ColumnAccessDeniedError, AuthorizationError)
        assert issubclass(JoinAccessDeniedError, AuthorizationError)
        assert issubclass(SqlSecurityError, AuthorizationError)

    def test_raising_exceptions(self) -> None:
        """Exceptions can be raised and caught as AuthorizationError."""
        with pytest.raises(AuthorizationError) as exc_info:
            raise ColumnAccessDeniedError("Column 'fixedCtc' cannot be aggregated.")
        assert "fixedCtc" in str(exc_info.value)
