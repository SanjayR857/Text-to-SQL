"""
Policy handler for Project, Allocation, Contract, and Milestone tables.
"""
from typing import Any

from auth.access_context import (
    AccessScope,
    ColumnPermission,
    ColumnSensitivity,
    TablePermission,
)
from auth.handlers.base_handler import (
    BasePolicyHandler,
)
from auth.predicate_spec import (
    PredicateOperator,
    PredicateSpec,
)
from auth.role import Role
from auth.user import UserContext

# Sensitive commercial and billing rate fields
_SENSITIVE_FINANCIAL_COLUMNS = {
    "value",
    "amount",
    "indiarateperhour",
    "billingrate",
    "margin",
    "profitpct",
}

# Column schemas
_PROJECT_NAME_COLUMNS = [
    "id",
    "projectName",
    "status",
    "projectStartDate",
    "projectEndDate",
    "billingType",
    "contractType",
    "currency",
]

_PROJECT_DETAIL_COLUMNS = [
    "id",
    "projectId",
    "resourceMailID",
    "reportingManager",
    "projectJoiningDate",
    "projectReleaseDate",
    "billability",
    "billabilityStartDate",
]

_PROJECT_DETAIL_HISTORY_COLUMNS = [
    "id",
    "eLevel",
    "hiringType",
    "billability",
    "changedAt",
    "changedBy",
    "billabilityStartDate",
    "indiaRatePerHour",
]

_CONTRACT_COLUMNS = [
    "id",
    "projectId",
    "contractName",
    "status",
    "contractType",
    "startDate",
    "endDate",
    "value",
]

_MILESTONE_COLUMNS = [
    "id",
    "projectId",
    "name",
    "amount",
    "dueDate",
    "status",
]

_CONTRACT_AMENDMENT_COLUMNS = [
    "id",
    "projectId",
    "type",
    "amount",
    "effectiveDate",
    "description",
]


class ProjectAccessHandler(BasePolicyHandler):
    """
    Enforces authorization on Project governance, contracts, allocations, and financials.

    - Admin / EP: Enterprise-wide visibility (ALL), full commercial metrics.
    - PMO: Full active project operational scope (PMO), operational columns.
    - Project Lead: Filtered to authorized project IDs (PROJECT), commercials hidden.
    - Employee / Dev: Self staffing allocation only (SELF), commercials hidden.
    """

    TABLE_COLUMNS = {
        "projectname": ("ProjectName", _PROJECT_NAME_COLUMNS),
        "projectdetail": ("ProjectDetail", _PROJECT_DETAIL_COLUMNS),
        "projectdetailhistory": ("ProjectDetailHistory", _PROJECT_DETAIL_HISTORY_COLUMNS),
        "contract": ("Contract", _CONTRACT_COLUMNS),
        "milestone": ("Milestone", _MILESTONE_COLUMNS),
        "contractamendment": ("ContractAmendment", _CONTRACT_AMENDMENT_COLUMNS),
    }

    def can_handle(self, table_name: str) -> bool:
        """Check if table is handled by ProjectAccessHandler."""
        return table_name.strip().lower() in self.TABLE_COLUMNS

    def resolve_table_permission(
        self,
        table_name: str,
        user_context: UserContext,
        parameters: dict[str, Any],
    ) -> TablePermission:
        """Resolve permissions and predicates for project-related tables."""
        clean_table = table_name.strip().lower()
        canonical_name, cols = self.TABLE_COLUMNS[clean_table]

        # Register execution parameters
        normalized_email = user_context.email.strip().lower()
        parameters["auth_user_email"] = normalized_email

        lead_projects = user_context.access_scope.project_ids
        parameters["auth_project_ids"] = lead_projects

        # 1. Platform Admin or Engagement Partner
        if user_context.is_ca_admin or user_context.has_role(Role.EP):
            return self._build_permission(
                canonical_name=canonical_name,
                cols=cols,
                scope=AccessScope.ALL,
                allow_commercials=True,
                predicates=[],
            )

        # 2. PMO (Cross-Module Operational Oversight via PMO vertical assignment)
        is_pmo = any(a.vertical_code.upper() == "PMO" for a in user_context.assignments)
        if is_pmo:
            return self._build_permission(
                canonical_name=canonical_name,
                cols=cols,
                scope=AccessScope.PMO,
                allow_commercials=True,
                predicates=[],
            )

        # 3. Project Lead (Restricted to assigned projects)
        is_lead = user_context.has_role(Role.LEAD)
        if is_lead and lead_projects:
            predicate = self._get_project_predicate(clean_table)
            return self._build_permission(
                canonical_name=canonical_name,
                cols=cols,
                scope=AccessScope.PROJECT,
                allow_commercials=False,
                predicates=[predicate],
            )
        elif is_lead and not lead_projects:
            # Lead with no active assigned projects -> default deny
            return self._build_permission(
                canonical_name=canonical_name,
                cols=cols,
                scope=AccessScope.NONE,
                allow_commercials=False,
                predicates=[PredicateSpec.deny()],
            )

        # 4. Standard Employee (Self Allocation)
        if clean_table == "projectdetail":
            predicate = PredicateSpec.for_self(
                column="resourceMailID",
                parameter_name="auth_user_email",
            )
            return self._build_permission(
                canonical_name=canonical_name,
                cols=cols,
                scope=AccessScope.SELF,
                allow_commercials=False,
                predicates=[predicate],
            )

        # For contracts/milestones/project details without Lead/PMO/Admin role -> Deny
        return TablePermission(
            table_name=canonical_name,
            can_read=False,
            scope=AccessScope.NONE,
            columns={},
            predicates=[PredicateSpec.deny()],
        )

    def _get_project_predicate(self, clean_table: str) -> PredicateSpec:
        """Derive the correct project-scoping predicate for the table."""
        col = "id" if clean_table == "projectname" else "projectId"
        return PredicateSpec(
            column=col,
            operator=PredicateOperator.IN,
            parameter_name="auth_project_ids",
        )

    def _build_permission(
        self,
        canonical_name: str,
        cols: list[str],
        scope: AccessScope,
        allow_commercials: bool,
        predicates: list[PredicateSpec],
    ) -> TablePermission:
        """Construct TablePermission with commercial redaction rules."""
        col_perms: dict[str, ColumnPermission] = {}

        for c in cols:
            is_sensitive = c.lower() in _SENSITIVE_FINANCIAL_COLUMNS
            col_perms[c.lower()] = self._col(
                name=c,
                sensitivity=ColumnSensitivity.CONFIDENTIAL if is_sensitive else ColumnSensitivity.INTERNAL,
                can_select=True if (not is_sensitive or allow_commercials) else False,
                can_filter=True if (not is_sensitive or allow_commercials) else False,
                can_join=True if (not is_sensitive or allow_commercials) else False,
                can_group=True if (not is_sensitive or allow_commercials) else False,
                can_aggregate=True if (not is_sensitive or allow_commercials) else False,
            )

        return TablePermission(
            table_name=canonical_name,
            can_read=scope != AccessScope.NONE,
            scope=scope,
            columns=col_perms,
            predicates=predicates,
        )
