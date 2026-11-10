"""
Policy handler for Demand requisitions and Talent Sourcing pipeline.
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

_SENSITIVE_RECRUITMENT_COLUMNS = {
    "currentctc",
    "expectedctc",
    "offeredctc",
    "noticeperiodbuyout",
}

_DEMAND_COLUMNS = [
    "id",
    "demandNumber",
    "demandYear",
    "yearNumber",
    "projectId",
    "demandName",
    "skillCode",
    "positionsOpen",
    "status",
]

_DEMAND_CANDIDATE_COLUMNS = [
    "id",
    "demandId",
    "sourcingRound",
    "source",
    "candidateName",
    "employeeMailId",
    "primarySkill",
    "experienceYears",
    "currentCtc",
    "expectedCtc",
    "status",
]

_PANEL_INFO_COLUMNS = [
    "id",
    "demandId",
    "interviewerEmail",
    "roundType",
    "scheduledAt",
]

_DEMAND_FEEDBACK_COLUMNS = [
    "id",
    "candidateId",
    "interviewerEmail",
    "recommendation",
    "technicalScore",
    "culturalScore",
    "feedback",
]


class DemandAccessHandler(BasePolicyHandler):
    """
    Enforces authorization on recruitment demands, candidate sourcing, and interview feedback.

    - Admin / EP / CHDMO Chief (Demand Office) / CHTAO Chief (Talent): Full pipeline access.
    - Interview Panelist / Employee: Can view open demands; candidate compensation strictly hidden.
    """

    TABLE_SCHEMAS = {
        "demand": ("Demand", _DEMAND_COLUMNS),
        "demandsourcinground": ("DemandSourcingRound", ["id", "demandId", "roundNo", "status"]),
        "demandcandidate": ("DemandCandidate", _DEMAND_CANDIDATE_COLUMNS),
        "panelinfo": ("PanelInfo", _PANEL_INFO_COLUMNS),
        "demandfeedback": ("DemandFeedback", _DEMAND_FEEDBACK_COLUMNS),
        "demandevent": ("DemandEvent", ["id", "demandId", "eventType", "createdAt"]),
    }

    def can_handle(self, table_name: str) -> bool:
        """Check if table is handled by DemandAccessHandler."""
        return table_name.strip().lower() in self.TABLE_SCHEMAS

    def resolve_table_permission(
        self,
        table_name: str,
        user_context: UserContext,
        parameters: dict[str, Any],
    ) -> TablePermission:
        """Resolve permissions for Demand and Recruitment tables."""
        clean_table = table_name.strip().lower()
        canonical_name, cols = self.TABLE_SCHEMAS[clean_table]

        # Check elevated recruitment roles (Admin, EP, CHDMO, CHTAO)
        is_recruitment_lead = (
            user_context.is_ca_admin
            or user_context.has_role(Role.EP)
            or any(
                a.role == Role.CHIEF and a.vertical_code.upper() in ("CHDMO", "CHTAO")
                for a in user_context.assignments
            )
        )

        if is_recruitment_lead:
            col_perms = {
                c.lower(): self._col(
                    name=c,
                    sensitivity=ColumnSensitivity.CONFIDENTIAL if c.lower() in _SENSITIVE_RECRUITMENT_COLUMNS else ColumnSensitivity.INTERNAL,
                    can_select=True,
                    can_filter=True,
                    can_join=True,
                    can_group=True,
                    can_aggregate=True,
                )
                for c in cols
            }
            return TablePermission(
                table_name=canonical_name,
                can_read=True,
                scope=AccessScope.ALL,
                columns=col_perms,
                predicates=[],
            )

        # Non-recruitment users: Demand table is open reference; candidates have compensation hidden
        col_perms = {}
        for c in cols:
            is_sensitive = c.lower() in _SENSITIVE_RECRUITMENT_COLUMNS
            col_perms[c.lower()] = self._col(
                name=c,
                sensitivity=ColumnSensitivity.CONFIDENTIAL if is_sensitive else ColumnSensitivity.INTERNAL,
                can_select=not is_sensitive,
                can_filter=not is_sensitive,
                can_join=True if not is_sensitive else False,
                can_group=not is_sensitive,
                can_aggregate=not is_sensitive,
            )

        return TablePermission(
            table_name=canonical_name,
            can_read=True,
            scope=AccessScope.VERTICAL,
            columns=col_perms,
            predicates=[],
        )
