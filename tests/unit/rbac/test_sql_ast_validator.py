"""
Unit tests for SqlAstValidator and SqlScopeResolver.
"""
from uuid import uuid4
import pytest
import sqlglot

from rbac import (
    AccessScope,
    ColumnPermission,
    ColumnSensitivity,
    ResolvedAccessContext,
    TablePermission,
)
from text_to_sql import (
    SqlAstValidator,
    SqlScopeResolver,
)
from core.exceptions import (
    ColumnAccessDeniedError,
    SqlSecurityError,
    TableAccessDeniedError,
)
from rbac.identity import (
    AccessScope as UserAccessScope,
    UserContext,
)


@pytest.fixture
def employee_access_context() -> ResolvedAccessContext:
    """Fixture creating access context for regular employee with sensitive fields restricted."""
    user = UserContext(
        user_id=uuid4(),
        email="emp@company.com",
        assignments=[],
        access_scope=UserAccessScope(vertical_codes=[], project_ids=[]),
    )

    emp_perm = TablePermission(
        table_name="EmployeeInformation",
        can_read=True,
        scope=AccessScope.SELF,
        columns={
            "id": ColumnPermission(
                column_name="id",
                can_select=True,
                can_filter=True,
                can_join=True,
                can_group=True,
                can_aggregate=True,
            ),
            "employeename": ColumnPermission(
                column_name="employeeName",
                can_select=True,
                can_filter=True,
                can_join=True,
                can_group=True,
                can_aggregate=False,
            ),
            "employeemailid": ColumnPermission(
                column_name="employeeMailId",
                can_select=True,
                can_filter=True,
                can_join=True,
                can_group=True,
                can_aggregate=False,
            ),
            "fixedctc": ColumnPermission(
                column_name="fixedCtc",
                sensitivity=ColumnSensitivity.CONFIDENTIAL,
                can_select=False,
                can_filter=False,
                can_join=False,
                can_group=False,
                can_aggregate=False,
            ),
            "performancescore": ColumnPermission(
                column_name="performanceScore",
                can_select=True,
                can_filter=True,
                can_aggregate=True,
            ),
        },
    )

    return ResolvedAccessContext(
        user_context=user,
        table_permissions={
            "employeeinformation": emp_perm,
        },
    )


class TestSqlAstValidator:
    """Tests verifying SqlAstValidator security rules."""

    def test_valid_select_query(self) -> None:
        """Valid analytical SELECT query passes validation."""
        validator = SqlAstValidator()
        sql = "SELECT id, LOWER(employeeName), COUNT(*) FROM EmployeeInformation GROUP BY id"
        ast = validator.validate_sql(sql)
        assert ast is not None

    def test_reject_mutating_dml(self) -> None:
        """INSERT, UPDATE, DELETE statements are strictly rejected."""
        validator = SqlAstValidator()
        with pytest.raises(SqlSecurityError, match="Mutating.*strictly forbidden"):
            validator.validate_sql("DELETE FROM EmployeeInformation WHERE id = 1")

        with pytest.raises(SqlSecurityError, match="Mutating.*strictly forbidden"):
            validator.validate_sql("UPDATE EmployeeInformation SET employeeName = 'hacked'")

        with pytest.raises(SqlSecurityError, match="Mutating.*strictly forbidden"):
            validator.validate_sql("INSERT INTO EmployeeInformation (id) VALUES (1)")

    def test_reject_mutating_ddl(self) -> None:
        """DROP, ALTER, CREATE statements are strictly rejected."""
        validator = SqlAstValidator()
        with pytest.raises(SqlSecurityError, match="Mutating.*strictly forbidden"):
            validator.validate_sql("DROP TABLE EmployeeInformation")

        with pytest.raises(SqlSecurityError, match="Mutating.*strictly forbidden"):
            validator.validate_sql("ALTER TABLE EmployeeInformation DROP COLUMN id")

    def test_reject_multi_statement_injection(self) -> None:
        """Semicolon chaining multiple statements is rejected."""
        validator = SqlAstValidator()
        with pytest.raises(SqlSecurityError, match="Multiple SQL statements detected"):
            validator.validate_sql("SELECT 1; DROP TABLE users;")

    def test_reject_prohibited_metadata_functions(self) -> None:
        """Functions probing database internals are strictly rejected."""
        validator = SqlAstValidator()
        with pytest.raises(SqlSecurityError, match="forbidden for security reasons"):
            validator.validate_sql("SELECT pg_sleep(5)")

        with pytest.raises(SqlSecurityError, match="forbidden for security reasons"):
            validator.validate_sql("SELECT current_user")

        with pytest.raises(SqlSecurityError, match="forbidden for security reasons"):
            validator.validate_sql("SELECT version()")

    def test_reject_system_catalog_schemas(self) -> None:
        """Access to pg_catalog or information_schema is forbidden."""
        validator = SqlAstValidator()
        with pytest.raises(SqlSecurityError, match="Direct access to system schema"):
            validator.validate_sql("SELECT * FROM pg_catalog.pg_tables")

        with pytest.raises(SqlSecurityError, match="Direct access to system schema"):
            validator.validate_sql("SELECT * FROM information_schema.tables")


class TestSqlScopeResolver:
    """Tests verifying SqlScopeResolver column permissions and wildcard expansion."""

    def test_reject_unauthorized_table(
        self, employee_access_context: ResolvedAccessContext
    ) -> None:
        """Accessing a table not permitted in access_context raises TableAccessDeniedError."""
        sql = "SELECT * FROM Scoreboard"
        ast = sqlglot.parse_one(sql)
        resolver = SqlScopeResolver()

        with pytest.raises(TableAccessDeniedError, match="Table 'Scoreboard' is not permitted"):
            resolver.resolve_and_validate(ast, employee_access_context)

    def test_wildcard_expansion(
        self, employee_access_context: ResolvedAccessContext
    ) -> None:
        """SELECT * is expanded only to permitted columns, omitting sensitive fields."""
        sql = "SELECT * FROM EmployeeInformation e"
        ast = sqlglot.parse_one(sql)
        resolver = SqlScopeResolver()

        transformed = resolver.resolve_and_validate(ast, employee_access_context)
        sql_out = transformed.sql().lower()

        # Permitted columns are expanded
        assert "e.id" in sql_out
        assert "e.employeename" in sql_out
        assert "e.employeemailid" in sql_out

        # Sensitive compensation is excluded from expansion
        assert "fixedctc" not in sql_out
        assert "*" not in sql_out

    def test_reject_sensitive_column_selection(
        self, employee_access_context: ResolvedAccessContext
    ) -> None:
        """Direct projection of can_select=False column raises ColumnAccessDeniedError."""
        sql = "SELECT fixedCtc FROM EmployeeInformation"
        ast = sqlglot.parse_one(sql)
        resolver = SqlScopeResolver()

        with pytest.raises(ColumnAccessDeniedError, match="cannot be projected"):
            resolver.resolve_and_validate(ast, employee_access_context)

    def test_reject_sensitive_column_filtering(
        self, employee_access_context: ResolvedAccessContext
    ) -> None:
        """Using can_filter=False column in WHERE raises ColumnAccessDeniedError (preventing inference)."""
        sql = "SELECT id FROM EmployeeInformation WHERE fixedCtc > 2000000"
        ast = sqlglot.parse_one(sql)
        resolver = SqlScopeResolver()

        with pytest.raises(ColumnAccessDeniedError, match="cannot be filtered"):
            resolver.resolve_and_validate(ast, employee_access_context)

    def test_reject_sensitive_column_grouping(
        self, employee_access_context: ResolvedAccessContext
    ) -> None:
        """Using can_group=False column in GROUP BY raises ColumnAccessDeniedError."""
        sql = "SELECT id, COUNT(*) FROM EmployeeInformation GROUP BY fixedCtc"
        ast = sqlglot.parse_one(sql)
        resolver = SqlScopeResolver()

        with pytest.raises(ColumnAccessDeniedError, match="cannot be grouped"):
            resolver.resolve_and_validate(ast, employee_access_context)

    def test_reject_sensitive_column_aggregations(
        self, employee_access_context: ResolvedAccessContext
    ) -> None:
        """All aggregate functions on sensitive columns are rejected."""
        resolver = SqlScopeResolver()

        # AVG
        with pytest.raises(ColumnAccessDeniedError, match="cannot be aggregated"):
            resolver.resolve_and_validate(
                sqlglot.parse_one("SELECT AVG(fixedCtc) FROM EmployeeInformation"),
                employee_access_context,
            )

        # SUM
        with pytest.raises(ColumnAccessDeniedError, match="cannot be aggregated"):
            resolver.resolve_and_validate(
                sqlglot.parse_one("SELECT SUM(fixedCtc) FROM EmployeeInformation"),
                employee_access_context,
            )

        # MIN / MAX
        with pytest.raises(ColumnAccessDeniedError, match="cannot be aggregated"):
            resolver.resolve_and_validate(
                sqlglot.parse_one("SELECT MIN(fixedCtc), MAX(fixedCtc) FROM EmployeeInformation"),
                employee_access_context,
            )

        # COUNT(col)
        with pytest.raises(ColumnAccessDeniedError, match="cannot be aggregated"):
            resolver.resolve_and_validate(
                sqlglot.parse_one("SELECT COUNT(fixedCtc) FROM EmployeeInformation"),
                employee_access_context,
            )

        # COUNT(DISTINCT col)
        with pytest.raises(ColumnAccessDeniedError, match="cannot be aggregated"):
            resolver.resolve_and_validate(
                sqlglot.parse_one("SELECT COUNT(DISTINCT fixedCtc) FROM EmployeeInformation"),
                employee_access_context,
            )

    def test_allowed_aggregations_succeed(
        self, employee_access_context: ResolvedAccessContext
    ) -> None:
        """COUNT(*) and aggregate on permitted column succeed."""
        resolver = SqlScopeResolver()

        # COUNT(*) has no column inside and succeeds
        ast1 = resolver.resolve_and_validate(
            sqlglot.parse_one("SELECT COUNT(*) FROM EmployeeInformation"),
            employee_access_context,
        )
        assert ast1 is not None

        # performanceScore has can_aggregate=True and succeeds
        ast2 = resolver.resolve_and_validate(
            sqlglot.parse_one("SELECT AVG(performanceScore) FROM EmployeeInformation"),
            employee_access_context,
        )
        assert ast2 is not None
