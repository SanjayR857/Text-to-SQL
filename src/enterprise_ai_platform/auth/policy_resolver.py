"""
Central Policy Resolver for the enterprise authorization engine.

Orchestrates table and column permission evaluation, row predicate generation,
and secure parameter binding across all domain policy handlers.
"""
from typing import Any

from enterprise_ai_platform.auth.access_context import (
    AccessScope,
    ResolvedAccessContext,
    TablePermission,
)
from enterprise_ai_platform.auth.handlers.attendance_handler import (
    AttendanceAccessHandler,
)
from enterprise_ai_platform.auth.handlers.base_handler import (
    BasePolicyHandler,
)
from enterprise_ai_platform.auth.handlers.demand_handler import (
    DemandAccessHandler,
)
from enterprise_ai_platform.auth.handlers.employee_handler import (
    EmployeeAccessHandler,
)
from enterprise_ai_platform.auth.handlers.project_handler import (
    ProjectAccessHandler,
)
from enterprise_ai_platform.auth.handlers.rating_comment_handler import (
    RatingCommentAccessHandler,
)
from enterprise_ai_platform.auth.handlers.scoreboard_handler import (
    ScoreboardAccessHandler,
)
from enterprise_ai_platform.auth.handlers.standard_vertical_handler import (
    StandardVerticalAccessHandler,
)
from enterprise_ai_platform.auth.predicate_spec import (
    PredicateSpec,
)
from enterprise_ai_platform.auth.user import UserContext


class PolicyResolver:
    """
    Evaluates enterprise RBAC permissions and constructs the ResolvedAccessContext.

    Dispatches table evaluation requests to specialized domain handlers while
    enforcing global security invariants (default-deny, parameter normalization).
    """

    def __init__(self, handlers: list[BasePolicyHandler] | None = None) -> None:
        """
        Initialize PolicyResolver with an ordered chain of policy handlers.

        Args:
            handlers: Custom list of policy handlers. If omitted, registers standard handlers.
        """
        self._handlers: list[BasePolicyHandler] = handlers or [
            EmployeeAccessHandler(),
            ProjectAccessHandler(),
            ScoreboardAccessHandler(),
            RatingCommentAccessHandler(),
            AttendanceAccessHandler(),
            DemandAccessHandler(),
            StandardVerticalAccessHandler(),
        ]

    def resolve_access_context(
        self,
        user_context: UserContext,
        requested_tables: list[str] | None = None,
    ) -> ResolvedAccessContext:
        """
        Compute effective permissions and bound parameters for the user session.

        Args:
            user_context: Authenticated caller identity and role assignments.
            requested_tables: Optional subset of table names to evaluate. If omitted,
                              evaluates all tables handled by registered handlers.

        Returns:
            Immutable ResolvedAccessContext containing table permissions and parameters.
        """
        # 1. Initialize normalized execution parameters
        normalized_email = user_context.email.strip().lower()
        normalized_verticals = [v.strip().upper() for v in user_context.access_scope.vertical_codes]
        project_ids = list(user_context.access_scope.project_ids)

        parameters: dict[str, Any] = {
            "auth_user_email": normalized_email,
            "auth_vertical_codes": normalized_verticals,
            "auth_project_ids": project_ids,
        }

        # 2. Determine tables to resolve
        tables_to_resolve = requested_tables
        if tables_to_resolve is None:
            tables_to_resolve = self.get_all_supported_tables()

        # 3. Resolve permissions for each table
        table_permissions: dict[str, TablePermission] = {}
        for tbl in tables_to_resolve:
            clean_tbl = tbl.strip().lower()
            handler = self._find_handler(clean_tbl)

            if handler is not None:
                perm = handler.resolve_table_permission(clean_tbl, user_context, parameters)
            else:
                # Default Deny for unregistered / unknown tables
                perm = TablePermission(
                    table_name=tbl,
                    can_read=False,
                    scope=AccessScope.NONE,
                    columns={},
                    predicates=[PredicateSpec.deny()],
                )

            table_permissions[clean_tbl] = perm

        return ResolvedAccessContext(
            user_context=user_context,
            table_permissions=table_permissions,
            parameters=parameters,
        )

    def _find_handler(self, table_name: str) -> BasePolicyHandler | None:
        """Find the first policy handler that can handle the table."""
        for handler in self._handlers:
            if handler.can_handle(table_name):
                return handler
        return None

    def get_all_supported_tables(self) -> list[str]:
        """Collect all canonical table names supported across registered handlers."""
        supported: set[str] = set()
        # Add primary known tables
        supported.update([
            "EmployeeInformation", "FirmContribution",
            "ProjectName", "ProjectDetail", "ProjectDetailHistory",
            "Milestone", "Contract", "ContractAmendment",
            "Scoreboard", "RatingComment",
            "OfficeAttendance", "OfficeAttendanceUpload",
            "Demand", "DemandCandidate", "PanelInfo", "DemandFeedback",
            "ChiefGoal", "PartnerGoal", "EmGoal", "KpiGoal",
            "AuditLog", "Vertical", "RoleAssignment",
        ])
        return sorted(supported)
