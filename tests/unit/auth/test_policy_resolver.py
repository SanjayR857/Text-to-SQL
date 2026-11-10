"""
Unit tests for PolicyResolver and domain policy handlers.
"""
from uuid import uuid4
import pytest

from enterprise_ai_platform.auth import (
    AccessScope,
    PolicyResolver,
    PredicateOperator,
)
from enterprise_ai_platform.auth.role import Area, Role
from enterprise_ai_platform.auth.user import (
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
def ep_user() -> UserContext:
    """Fixture for Engagement Partner."""
    return UserContext(
        user_id=uuid4(),
        email="ep@company.com",
        assignments=[
            RoleAssignmentContext(
                role=Role.EP,
                vertical_code="CA",
                vertical_name="Central Application",
                vertical_area=Area.CentralApplication,
            )
        ],
        access_scope=UserAccessScope(vertical_codes=["CA"], project_ids=[]),
    )


@pytest.fixture
def chtao_chief_user() -> UserContext:
    """Fixture for Talent Chief (CHTAO)."""
    return UserContext(
        user_id=uuid4(),
        email="talent.chief@company.com",
        assignments=[
            RoleAssignmentContext(
                role=Role.CHIEF,
                vertical_code="CHTAO",
                vertical_name="Chief Talent Office",
                vertical_area=Area.IndividualModule,
            )
        ],
        access_scope=UserAccessScope(vertical_codes=["CHTAO"], project_ids=[]),
    )


@pytest.fixture
def chdlo_lead_user() -> UserContext:
    """Fixture for Delivery Lead (CHDLO) assigned to two projects."""
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
        access_scope=UserAccessScope(
            vertical_codes=["CHDLO"],
            project_ids=["proj-uuid-1", "proj-uuid-2"],
        ),
    )


@pytest.fixture
def unassigned_employee_user() -> UserContext:
    """Fixture for regular employee with only SELF scope."""
    return UserContext(
        user_id=uuid4(),
        email="john.doe@company.com",
        assignments=[],
        access_scope=UserAccessScope(vertical_codes=[], project_ids=[]),
    )


class TestPolicyResolverAdminAndEP:
    """Tests verifying CA Admin and Engagement Partner privileges."""

    def test_ca_admin_unrestricted_access(self, ca_admin_user: UserContext) -> None:
        """CA Admin receives ALL scope across Employee, Project, and Scoreboard tables."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(ca_admin_user)

        # 1. EmployeeInformation
        emp_perm = ctx.get_table_permission("EmployeeInformation")
        assert emp_perm is not None
        assert emp_perm.can_read
        assert emp_perm.scope == AccessScope.ALL
        assert "fixedctc" in emp_perm.allowed_select_columns
        assert "fixedctc" in emp_perm.allowed_aggregate_columns
        assert len(emp_perm.predicates) == 0

        # 2. Scoreboard
        score_perm = ctx.get_table_permission("Scoreboard")
        assert score_perm is not None
        assert score_perm.can_read
        assert score_perm.scope == AccessScope.ALL

        # 3. ProjectName and Contract commercials
        contract_perm = ctx.get_table_permission("Contract")
        assert contract_perm is not None
        assert contract_perm.can_read
        assert "value" in contract_perm.allowed_select_columns
        assert "value" in contract_perm.allowed_aggregate_columns

    def test_ep_scoreboard_access(self, ep_user: UserContext) -> None:
        """Engagement Partner is explicitly granted ALL scope to Scoreboard."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(ep_user)

        score_perm = ctx.get_table_permission("Scoreboard")
        assert score_perm is not None
        assert score_perm.can_read
        assert score_perm.scope == AccessScope.ALL
        assert "score" in score_perm.allowed_select_columns
        assert "rank" in score_perm.allowed_select_columns


class TestPolicyResolverVerticalChief:
    """Tests verifying vertical Chief authorization boundaries."""

    def test_chtao_chief_employee_scoping(self, chtao_chief_user: UserContext) -> None:
        """CHTAO Chief has VERTICAL scope on EmployeeInformation, but compensation is masked."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(chtao_chief_user)

        emp_perm = ctx.get_table_permission("EmployeeInformation")
        assert emp_perm is not None
        assert emp_perm.can_read
        assert emp_perm.scope == AccessScope.VERTICAL
        assert "employeename" in emp_perm.allowed_select_columns
        assert "highestqualification" in emp_perm.allowed_select_columns

        # Compensation is masked
        assert "fixedctc" not in emp_perm.allowed_select_columns
        assert "fixedctc" not in emp_perm.allowed_aggregate_columns

    def test_chtao_chief_denied_scoreboard(self, chtao_chief_user: UserContext) -> None:
        """Vertical Chiefs are strictly denied access to the Scoreboard."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(chtao_chief_user)

        score_perm = ctx.get_table_permission("Scoreboard")
        assert score_perm is not None
        assert not score_perm.can_read
        assert score_perm.scope == AccessScope.NONE


class TestPolicyResolverProjectLead:
    """Tests verifying Project Lead authorization scoping."""

    def test_chdlo_lead_project_scoping(self, chdlo_lead_user: UserContext) -> None:
        """Project Lead is restricted to assigned project IDs and commercials are redacted."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(chdlo_lead_user)

        # 1. ProjectName
        proj_perm = ctx.get_table_permission("ProjectName")
        assert proj_perm is not None
        assert proj_perm.can_read
        assert proj_perm.scope == AccessScope.PROJECT
        assert len(proj_perm.predicates) == 1
        assert proj_perm.predicates[0].operator == PredicateOperator.IN
        assert proj_perm.predicates[0].parameter_name == "auth_project_ids"

        # Parameters contains the project UUIDs
        assert ctx.parameters["auth_project_ids"] == ["proj-uuid-1", "proj-uuid-2"]

        # 2. Contract financials are redacted
        contract_perm = ctx.get_table_permission("Contract")
        assert contract_perm is not None
        assert contract_perm.can_read
        assert "value" not in contract_perm.allowed_select_columns
        assert "value" not in contract_perm.allowed_aggregate_columns


class TestPolicyResolverUnassignedEmployee:
    """Tests verifying regular Employee (SELF) access constraints."""

    def test_employee_self_scope_on_employee_info(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Regular employee only has SELF access on EmployeeInformation with compensation hidden."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)

        emp_perm = ctx.get_table_permission("EmployeeInformation")
        assert emp_perm is not None
        assert emp_perm.can_read
        assert emp_perm.scope == AccessScope.SELF

        # Identity predicate bound to caller email
        assert len(emp_perm.predicates) == 1
        assert emp_perm.predicates[0].operator == PredicateOperator.EQ
        assert emp_perm.predicates[0].column == "employeeMailId"
        assert emp_perm.predicates[0].parameter_name == "auth_user_email"
        assert ctx.parameters["auth_user_email"] == "john.doe@company.com"

        # Operational fields allowed
        assert "employeename" in emp_perm.allowed_select_columns
        assert "employeecode" in emp_perm.allowed_select_columns

        # Confidential compensation completely hidden
        assert "fixedctc" not in emp_perm.allowed_select_columns
        assert "fixedctc" not in emp_perm.allowed_filter_columns
        assert "fixedctc" not in emp_perm.allowed_aggregate_columns
        assert "variablectc" not in emp_perm.allowed_select_columns
        assert "currentctc" not in emp_perm.allowed_select_columns

    def test_employee_attendance_self_scoping(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Regular employee only has SELF access on OfficeAttendance."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)

        att_perm = ctx.get_table_permission("OfficeAttendance")
        assert att_perm is not None
        assert att_perm.can_read
        assert att_perm.scope == AccessScope.SELF
        assert len(att_perm.predicates) == 1
        assert att_perm.predicates[0].column == "employeeMailId"

    def test_employee_scoreboard_and_audit_denied(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Regular employee is denied access to Scoreboard, AuditLog, and AttendanceUpload."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(unassigned_employee_user)

        assert not ctx.is_table_accessible("Scoreboard")
        assert not ctx.is_table_accessible("AuditLog")
        assert not ctx.is_table_accessible("OfficeAttendanceUpload")

    def test_unknown_table_default_deny(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Unknown or unregistered tables are denied by default."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["NonExistentTable"],
        )

        assert not ctx.is_table_accessible("NonExistentTable")
        perm = ctx.get_table_permission("NonExistentTable")
        assert perm is not None
        assert not perm.can_read
        assert perm.scope == AccessScope.NONE


class TestPolicyResolverDomainHandlers:
    """Tests verifying Demand, RatingComment, and parameter normalization."""

    def test_demand_candidate_ctc_masked_for_non_recruitment(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Non-recruitment employees cannot select, filter, or aggregate candidate CTC."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["DemandCandidate"],
        )

        cand_perm = ctx.get_table_permission("DemandCandidate")
        assert cand_perm is not None
        assert cand_perm.can_read
        assert "candidatename" in cand_perm.allowed_select_columns
        assert "currentctc" not in cand_perm.allowed_select_columns
        assert "currentctc" not in cand_perm.allowed_filter_columns
        assert "currentctc" not in cand_perm.allowed_aggregate_columns
        assert "expectedctc" not in cand_perm.allowed_select_columns

    def test_demand_candidate_ctc_visible_for_chdmo_chief(self) -> None:
        """CHDMO Chief (Demand Office) has full access including candidate compensation."""
        user = UserContext(
            user_id=uuid4(),
            email="demand.chief@company.com",
            assignments=[
                RoleAssignmentContext(
                    role=Role.CHIEF,
                    vertical_code="CHDMO",
                    vertical_name="Chief Demand Office",
                    vertical_area=Area.IndividualModule,
                )
            ],
            access_scope=UserAccessScope(vertical_codes=["CHDMO"], project_ids=[]),
        )
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            user,
            requested_tables=["DemandCandidate"],
        )

        cand_perm = ctx.get_table_permission("DemandCandidate")
        assert cand_perm is not None
        assert cand_perm.can_read
        assert "currentctc" in cand_perm.allowed_select_columns
        assert "currentctc" in cand_perm.allowed_aggregate_columns

    def test_rating_comment_self_scoping(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Regular employee only has access to rating comments directed at their own email."""
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["RatingComment"],
        )

        perm = ctx.get_table_permission("RatingComment")
        assert perm is not None
        assert perm.can_read
        assert perm.scope == AccessScope.SELF
        assert len(perm.predicates) == 1
        assert perm.predicates[0].column == "rateeEmail"
        assert perm.predicates[0].operator == PredicateOperator.EQ
        assert perm.predicates[0].parameter_name == "auth_user_email"

    def test_parameter_normalization(self) -> None:
        """Parameters are strictly normalized to prevent case-mismatch bypasses."""
        user = UserContext(
            user_id=uuid4(),
            email="  AlICe.SMiTH@Company.COM  ",
            assignments=[
                RoleAssignmentContext(
                    role=Role.CHIEF,
                    vertical_code="chdlo",
                    vertical_name="Chief Delivery Office",
                    vertical_area=Area.IndividualModule,
                )
            ],
            access_scope=UserAccessScope(vertical_codes=["chdlo"], project_ids=["proj-1"]),
        )
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(user)

        assert ctx.parameters["auth_user_email"] == "alice.smith@company.com"
        assert ctx.parameters["auth_vertical_codes"] == ["CHDLO"]
        assert ctx.parameters["auth_project_ids"] == ["proj-1"]

    def test_standard_vertical_goal_scoping(self) -> None:
        """ChiefGoal is scoped to user's assigned vertical code."""
        user = UserContext(
            user_id=uuid4(),
            email="chief@company.com",
            assignments=[
                RoleAssignmentContext(
                    role=Role.CHIEF,
                    vertical_code="CHAIO",
                    vertical_name="Central AI Office",
                    vertical_area=Area.IndividualModule,
                )
            ],
            access_scope=UserAccessScope(vertical_codes=["CHAIO"], project_ids=[]),
        )
        resolver = PolicyResolver()
        ctx = resolver.resolve_access_context(
            user,
            requested_tables=["ChiefGoal"],
        )

        goal_perm = ctx.get_table_permission("ChiefGoal")
        assert goal_perm is not None
        assert goal_perm.can_read
        assert goal_perm.scope == AccessScope.VERTICAL
        assert len(goal_perm.predicates) == 1
        assert goal_perm.predicates[0].column == "verticalCode"
        assert goal_perm.predicates[0].operator == PredicateOperator.IN
        assert goal_perm.predicates[0].parameter_name == "auth_vertical_codes"

