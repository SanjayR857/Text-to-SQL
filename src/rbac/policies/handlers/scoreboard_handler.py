"""
Policy handler for Scoreboard leaderboards and rankings.
"""
from typing import Any

from rbac.policies.access_context import (
    AccessScope,
    ColumnPermission,
    ColumnSensitivity,
    TablePermission,
)
from rbac.policies.handlers.base_handler import (
    BasePolicyHandler,
)
from rbac.policies.predicate_spec import (
    PredicateSpec,
)
from rbac.identity.role import Role
from rbac.identity.user import UserContext

_SCOREBOARD_COLUMNS = [
    "id",
    "employeeMailId",
    "employeeName",
    "verticalCode",
    "appraisalYearId",
    "quarter",
    "score",
    "rank",
    "deliveryScore",
    "orgScore",
]


class ScoreboardAccessHandler(BasePolicyHandler):
    """
    Enforces authorization on the Scoreboard view.

    Strict rule: Only the Engagement Partner (EP) and Central Application Admin (CA ADMIN)
    are authorized to access ranked scoreboards and leaderboards.
    All other personas (Chiefs, Leads, Employees) are strictly denied access.
    """

    SUPPORTED_TABLES = {"scoreboard"}

    def can_handle(self, table_name: str) -> bool:
        """Check if table is handled by ScoreboardAccessHandler."""
        return table_name.strip().lower() in self.SUPPORTED_TABLES

    def resolve_table_permission(
        self,
        table_name: str,
        user_context: UserContext,
        parameters: dict[str, Any],
    ) -> TablePermission:
        """Resolve permissions for the Scoreboard table."""
        # 1. Only CA ADMIN or EP role may read the scoreboard
        if user_context.is_ca_admin or user_context.has_role(Role.EP):
            col_perms: dict[str, ColumnPermission] = {
                c.lower(): self._col(
                    name=c,
                    sensitivity=ColumnSensitivity.RESTRICTED,
                    can_select=True,
                    can_filter=True,
                    can_join=True,
                    can_group=True,
                    can_aggregate=True,
                )
                for c in _SCOREBOARD_COLUMNS
            }
            return TablePermission(
                table_name="Scoreboard",
                can_read=True,
                scope=AccessScope.ALL,
                columns=col_perms,
                predicates=[],
            )

        # 2. Strict Default Deny for all other roles
        return TablePermission(
            table_name="Scoreboard",
            can_read=False,
            scope=AccessScope.NONE,
            columns={},
            predicates=[PredicateSpec.deny()],
        )
