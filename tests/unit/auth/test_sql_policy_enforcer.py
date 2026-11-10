"""
Comprehensive unit tests for SqlPolicyEnforcer and RowPredicateInjector.
"""
from uuid import uuid4
import pytest

from auth import (
    AccessScope,
    PolicyResolver,
)
from text_to_sql import (
    RowPredicateInjector,
    SqlPolicyEnforcer,
)
from core.exceptions import (
    ColumnAccessDeniedError,
    JoinAccessDeniedError,
    TableAccessDeniedError,
)
from auth.role import Area, Role
from auth.user import (
    AccessScope as UserAccessScope,
    RoleAssignmentContext,
    UserContext,
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


@pytest.fixture
def chdlo_lead_user() -> UserContext:
    """Fixture for Delivery Lead assigned to project proj-101."""
    return UserContext(
        user_id=uuid4(),
        email="lead@company.com",
        assignments=[
            RoleAssignmentContext(
                role=Role.LEAD,
                vertical_code="CHDLO",
                vertical_name="Chief Delivery Office",
                vertical_area=Area.IndividualModule,
            )
        ],
        access_scope=UserAccessScope(vertical_codes=["CHDLO"], project_ids=["proj-101"]),
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


class TestSqlPolicyEnforcerDirectQueries:
    """Tests verifying direct query enforcement and row predicate injection."""

    def test_self_scope_where_injection(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Direct query by regular employee has SELF identity predicate injected."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)
        enforcer = SqlPolicyEnforcer()

        sql = "SELECT id, employeeName FROM EmployeeInformation WHERE highestQualification = 'PhD'"
        enforced_sql, params = enforcer.enforce_policy(sql, ctx)

        sql_lower = enforced_sql.lower()
        assert "highestqualification = 'phd'" in sql_lower
        assert "employeeinformation.employeemailid = :auth_user_email" in sql_lower
        assert params["auth_user_email"] == "john.doe@company.com"

    def test_self_scope_count_aggregation(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """COUNT(*) under SELF scope has predicate injected before aggregation."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)
        enforcer = SqlPolicyEnforcer()

        sql = "SELECT COUNT(*) FROM EmployeeInformation"
        enforced_sql, params = enforcer.enforce_policy(sql, ctx)

        sql_lower = enforced_sql.lower()
        assert "select count(*)" in sql_lower
        assert "employeeinformation.employeemailid = :auth_user_email" in sql_lower
        assert params["auth_user_email"] == "john.doe@company.com"


class TestSqlPolicyEnforcerOuterJoins:
    """Tests verifying outer join preservation via prefiltered derived subqueries."""

    def test_outer_join_preservation(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """LEFT JOIN target is rewritten into a derived subquery, preserving outer semantics."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)
        enforcer = SqlPolicyEnforcer()

        # ProjectDetail (self allocated) joined with EmployeeInformation
        sql = (
            "SELECT d.id, e.employeeName "
            "FROM ProjectDetail d "
            "LEFT JOIN EmployeeInformation e ON d.resourceMailID = e.employeeMailId"
        )
        enforced_sql, params = enforcer.enforce_policy(sql, ctx)

        sql_lower = enforced_sql.lower()
        # Verify LEFT JOIN uses derived subquery
        assert "left join (select * from employeeinformation" in sql_lower
        assert "where employeeinformation.employeemailid = :auth_user_email" in sql_lower
        assert ") as e on" in sql_lower


class TestSqlPolicyEnforcerCteQueries:
    """Tests verifying CTE and subquery scope handling."""

    def test_cte_predicate_injection(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Predicates are injected at the CTE definition level."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)
        enforcer = SqlPolicyEnforcer()

        sql = (
            "WITH my_team AS ("
            "    SELECT id, employeeName FROM EmployeeInformation"
            ") "
            "SELECT * FROM my_team"
        )
        enforced_sql, params = enforcer.enforce_policy(sql, ctx)

        sql_lower = enforced_sql.lower()
        assert "where employeeinformation.employeemailid = :auth_user_email" in sql_lower


class TestSqlPolicyEnforcerSecurityViolations:
    """Tests verifying security rejection gates in the enforcement pipeline."""

    def test_reject_unauthorized_table(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Accessing Scoreboard by employee raises TableAccessDeniedError."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)
        enforcer = SqlPolicyEnforcer()

        sql = "SELECT * FROM Scoreboard"
        with pytest.raises(TableAccessDeniedError):
            enforcer.enforce_policy(sql, ctx)

    def test_reject_sensitive_column_inference(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Filtering or aggregating on confidential compensation raises ColumnAccessDeniedError."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)
        enforcer = SqlPolicyEnforcer()

        # In WHERE clause
        with pytest.raises(ColumnAccessDeniedError, match="cannot be filtered"):
            enforcer.enforce_policy(
                "SELECT id FROM EmployeeInformation WHERE fixedCtc > 2000000",
                ctx,
            )

        # In Aggregate
        with pytest.raises(ColumnAccessDeniedError, match="cannot be aggregated"):
            enforcer.enforce_policy(
                "SELECT AVG(fixedCtc) FROM EmployeeInformation",
                ctx,
            )

    def test_reject_join_bypass_attack(
        self, chdlo_lead_user: UserContext
    ) -> None:
        """JOIN condition with OR 1=1 raises JoinAccessDeniedError."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(chdlo_lead_user)
        enforcer = SqlPolicyEnforcer()

        sql = (
            "SELECT p.projectName, d.resourceMailID "
            "FROM ProjectName p "
            "JOIN ProjectDetail d ON p.id = d.projectId OR 1=1"
        )
        with pytest.raises(JoinAccessDeniedError, match="OR disjunctions"):
            enforcer.enforce_policy(sql, ctx)


class TestSqlPolicyEnforcerAdminUnrestricted:
    """Tests verifying CA Admin full access without predicate injection."""

    def test_admin_no_predicates_injected(
        self, ca_admin_user: UserContext
    ) -> None:
        """CA Admin with ALL scope has no row predicates injected."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(ca_admin_user)
        enforcer = SqlPolicyEnforcer()

        sql = "SELECT id, employeeName, fixedCtc FROM EmployeeInformation"
        enforced_sql, params = enforcer.enforce_policy(sql, ctx)

        sql_lower = enforced_sql.lower()
        assert "where" not in sql_lower
        assert "fixedctc" in sql_lower

    def test_project_lead_multi_table_scope_injection(
        self, chdlo_lead_user: UserContext
    ) -> None:
        """Both joined tables in Project Lead query have project-scoping predicates injected."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(chdlo_lead_user)
        enforcer = SqlPolicyEnforcer()

        sql = (
            "SELECT p.projectName, d.resourceMailID "
            "FROM ProjectName p "
            "JOIN ProjectDetail d ON p.id = d.projectId"
        )
        enforced_sql, params = enforcer.enforce_policy(sql, ctx)

        sql_lower = enforced_sql.lower()
        assert "p.id in (:auth_project_ids)" in sql_lower
        assert "d.projectid in (:auth_project_ids)" in sql_lower
        assert params["auth_project_ids"] == ["proj-101"]

    def test_employee_wildcard_expansion_via_enforcer(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """SELECT * via enforcer expands explicit non-sensitive columns and injects SELF predicate."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)
        enforcer = SqlPolicyEnforcer()

        sql = "SELECT * FROM EmployeeInformation e"
        enforced_sql, params = enforcer.enforce_policy(sql, ctx)

        sql_lower = enforced_sql.lower()
        assert "e.id" in sql_lower
        assert "e.employeename" in sql_lower
        assert "fixedctc" not in sql_lower
        assert "e.employeemailid = :auth_user_email" in sql_lower

    def test_attendance_count_self_scoping(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Employee count query on OfficeAttendance is scoped to caller email."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)
        enforcer = SqlPolicyEnforcer()

        sql = "SELECT COUNT(*) FROM OfficeAttendance WHERE swipeDate >= '2026-11-01'"
        enforced_sql, params = enforcer.enforce_policy(sql, ctx)

        sql_lower = enforced_sql.lower()
        assert "select count(*)" in sql_lower
        assert "officeattendance.employeemailid = :auth_user_email" in sql_lower
        assert params["auth_user_email"] == "john.doe@company.com"
