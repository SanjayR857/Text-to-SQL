"""
Unit tests for ApprovedJoinEdge and JoinGraphValidator.
"""
from uuid import uuid4
import pytest
import sqlglot

from auth import (
    AccessScope,
    ApprovedJoinEdge,
    ColumnPermission,
    JoinGraphValidator,
    ResolvedAccessContext,
    TablePermission,
)
from core.exceptions import JoinAccessDeniedError
from auth.user import (
    AccessScope as UserAccessScope,
    UserContext,
)


@pytest.fixture
def sample_access_context() -> ResolvedAccessContext:
    """Fixture creating access context with ProjectName, ProjectDetail, and Contract."""
    user = UserContext(
        user_id=uuid4(),
        email="lead@company.com",
        assignments=[],
        access_scope=UserAccessScope(vertical_codes=[], project_ids=[]),
    )

    proj_perm = TablePermission(
        table_name="ProjectName",
        can_read=True,
        scope=AccessScope.ALL,
        columns={
            "id": ColumnPermission(column_name="id", can_select=True, can_join=True),
            "projectname": ColumnPermission(column_name="projectName", can_select=True),
        },
    )
    detail_perm = TablePermission(
        table_name="ProjectDetail",
        can_read=True,
        scope=AccessScope.ALL,
        columns={
            "id": ColumnPermission(column_name="id", can_select=True),
            "projectid": ColumnPermission(column_name="projectId", can_select=True, can_join=True),
            "resourcemailid": ColumnPermission(column_name="resourceMailID", can_select=True, can_join=True),
        },
    )
    contract_perm = TablePermission(
        table_name="Contract",
        can_read=True,
        scope=AccessScope.ALL,
        columns={
            "id": ColumnPermission(column_name="id", can_select=True),
            "projectid": ColumnPermission(column_name="projectId", can_select=True, can_join=True),
            "contractname": ColumnPermission(column_name="contractName", can_select=True),
        },
    )
    emp_perm = TablePermission(
        table_name="EmployeeInformation",
        can_read=True,
        scope=AccessScope.SELF,
        columns={
            "id": ColumnPermission(column_name="id", can_select=True, can_join=False),
            "employeemailid": ColumnPermission(column_name="employeeMailId", can_select=True, can_join=True),
        },
    )

    return ResolvedAccessContext(
        user_context=user,
        table_permissions={
            "projectname": proj_perm,
            "projectdetail": detail_perm,
            "contract": contract_perm,
            "employeeinformation": emp_perm,
        },
    )


class TestApprovedJoinEdge:
    """Tests verifying ApprovedJoinEdge matching behavior."""

    def test_symmetric_matching(self) -> None:
        """Join edge matches symmetrically regardless of left/right position."""
        edge = ApprovedJoinEdge(
            source_table="ProjectName",
            source_column="id",
            target_table="ProjectDetail",
            target_column="projectId",
        )

        assert edge.matches("ProjectName", "id", "ProjectDetail", "projectId")
        assert edge.matches("ProjectDetail", "projectId", "ProjectName", "id")

    def test_case_insensitive_matching(self) -> None:
        """Join edge matching is case-insensitive."""
        edge = ApprovedJoinEdge(
            source_table="ProjectName",
            source_column="id",
            target_table="ProjectDetail",
            target_column="projectId",
        )

        assert edge.matches("PROJECTNAME", "ID", "projectdetail", "projectid")
        assert not edge.matches("ProjectName", "name", "ProjectDetail", "projectId")


class TestJoinGraphValidator:
    """Tests verifying JoinGraphValidator enforcement rules."""

    def test_valid_approved_inner_join(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """Approved join between ProjectName and ProjectDetail succeeds."""
        sql = (
            "SELECT p.projectName, d.resourceMailID "
            "FROM ProjectName p "
            "JOIN ProjectDetail d ON p.id = d.projectId"
        )
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        # Should pass without raising
        validator.validate_joins(ast, sample_access_context)

    def test_valid_approved_left_join(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """Approved LEFT JOIN between ProjectName and Contract succeeds."""
        sql = (
            "SELECT p.projectName, c.contractName "
            "FROM ProjectName p "
            "LEFT JOIN Contract c ON p.id = c.projectId"
        )
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        validator.validate_joins(ast, sample_access_context)

    def test_reject_unapproved_join(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """Arbitrary join between unapproved tables is rejected."""
        sql = (
            "SELECT e.employeeMailId, c.contractName "
            "FROM EmployeeInformation e "
            "JOIN Contract c ON e.employeeMailId = c.projectId"
        )
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        with pytest.raises(JoinAccessDeniedError, match="not approved"):
            validator.validate_joins(ast, sample_access_context)

    def test_reject_or_bypass_attack(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """Join ON condition containing OR 1=1 is strictly rejected."""
        sql = (
            "SELECT p.projectName, d.resourceMailID "
            "FROM ProjectName p "
            "JOIN ProjectDetail d ON p.id = d.projectId OR 1=1"
        )
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        with pytest.raises(JoinAccessDeniedError, match="OR disjunctions.*forbidden"):
            validator.validate_joins(ast, sample_access_context)

    def test_reject_cross_join(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """CROSS JOIN operations are strictly forbidden."""
        sql = "SELECT * FROM ProjectName CROSS JOIN Contract"
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        with pytest.raises(JoinAccessDeniedError, match="CROSS JOIN.*forbidden"):
            validator.validate_joins(ast, sample_access_context)

    def test_reject_comma_cartesian_join(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """Implicit comma join (FROM A, B) is strictly forbidden."""
        sql = "SELECT * FROM ProjectName, Contract"
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        with pytest.raises(JoinAccessDeniedError, match="Cartesian products are forbidden"):
            validator.validate_joins(ast, sample_access_context)

    def test_reject_join_missing_on_condition(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """JOIN missing an ON clause is rejected."""
        sql = "SELECT * FROM ProjectName JOIN Contract"
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        with pytest.raises(JoinAccessDeniedError, match="Join missing ON condition"):
            validator.validate_joins(ast, sample_access_context)

    def test_reject_column_without_can_join(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """Joining on a column where can_join is False is rejected."""
        # EmployeeInformation.id has can_join=False in fixture
        sql = (
            "SELECT * FROM ProjectName p "
            "JOIN EmployeeInformation e ON p.id = e.id"
        )
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        with pytest.raises(JoinAccessDeniedError, match="not authorized for JOIN operations"):
            validator.validate_joins(ast, sample_access_context)

    def test_reject_inaccessible_table_in_join(
        self, sample_access_context: ResolvedAccessContext
    ) -> None:
        """Joining an unpermitted table is rejected."""
        sql = (
            "SELECT * FROM ProjectName p "
            "JOIN NonExistentTable n ON p.id = n.projectId"
        )
        ast = sqlglot.parse_one(sql)
        validator = JoinGraphValidator()

        with pytest.raises(JoinAccessDeniedError, match="inaccessible table"):
            validator.validate_joins(ast, sample_access_context)

    def test_prompt_hints_generation(self) -> None:
        """Prompt join hints accurately format available edges."""
        validator = JoinGraphValidator()
        hints = validator.format_join_hints_for_prompt({"ProjectName", "ProjectDetail"})

        assert "ProjectName.id = ProjectDetail.projectId" in hints
        assert "Approved Table Join Relationships" in hints

        # Empty tables produces empty string
        assert validator.format_join_hints_for_prompt({"UnknownTable"}) == ""
