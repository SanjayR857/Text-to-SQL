"""
Policy handler for Employee Information and Firm Contribution tables.
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

# Sensitive columns completely hidden from regular employees
_SENSITIVE_COMPENSATION_COLUMNS = {
    "currentctc",
    "fixedctc",
    "variablectc",
    "previousctc",
    "expectedctc",
    "pannumber",
    "passportnumber",
    "bankaccountnumber",
    "bankifsccode",
}

# Standard operational columns for EmployeeInformation
_EMPLOYEE_COLUMNS = [
    "id",
    "employeeName",
    "employeeMailId",
    "employeeCode",
    "mobileNumber",
    "personalEmailId",
    "dateOfBirth",
    "highestQualification",
    "careerLevel",
    "designation",
    "department",
    "workLocation",
    "joiningDate",
    "reportingManagerMailId",
    "currentCtc",
    "fixedCtc",
    "variableCtc",
    "panNumber",
    "passportNumber",
]

# Columns for FirmContribution
_FIRM_CONTRIBUTION_COLUMNS = [
    "id",
    "employeeMailId",
    "activityName",
    "contributionType",
    "startDate",
    "endDate",
    "details",
    "numberOfHours",
    "numberOfPeople",
    "status",
]


class EmployeeAccessHandler(BasePolicyHandler):
    """
    Enforces authorization on Employee directory and firm contribution records.

    Tier 1 (Admin / EP): Enterprise-wide access (ALL).
    Tier 2 (CHTAO Chief): Full talent directory (VERTICAL), sensitive compensation masked.
    Tier 3 (Employee / Self): Personal record only (SELF), sensitive fields completely hidden.
    """

    SUPPORTED_TABLES = {"employeeinformation", "firmcontribution"}

    def can_handle(self, table_name: str) -> bool:
        """Check if table is handled by EmployeeAccessHandler."""
        return table_name.strip().lower() in self.SUPPORTED_TABLES

    def resolve_table_permission(
        self,
        table_name: str,
        user_context: UserContext,
        parameters: dict[str, Any],
    ) -> TablePermission:
        """Resolve permissions and row predicates for Employee tables."""
        clean_table = table_name.strip().lower()

        # Always bind normalized identity email
        normalized_email = user_context.email.strip().lower()
        parameters["auth_user_email"] = normalized_email

        # 1. Tier 1: Platform Admin or Engagement Partner
        if user_context.is_ca_admin or user_context.has_role(Role.EP):
            return self._build_admin_permission(clean_table)

        # 2. Tier 2: CHTAO Chief (Talent Office Leadership)
        is_chtao_chief = any(
            a.role == Role.CHIEF and a.vertical_code.upper() == "CHTAO"
            for a in user_context.assignments
        )
        if is_chtao_chief:
            return self._build_talent_chief_permission(clean_table)

        # 3. Tier 3: Self Access (Unassigned employee or non-talent verticals)
        return self._build_self_permission(clean_table, normalized_email)

    def _build_admin_permission(self, table_name: str) -> TablePermission:
        """Construct unrestricted TablePermission for Admin / EP."""
        cols = _EMPLOYEE_COLUMNS if table_name == "employeeinformation" else _FIRM_CONTRIBUTION_COLUMNS
        col_perms: dict[str, ColumnPermission] = {
            c.lower(): self._col(
                name=c,
                sensitivity=ColumnSensitivity.CONFIDENTIAL if c.lower() in _SENSITIVE_COMPENSATION_COLUMNS else ColumnSensitivity.INTERNAL,
                can_select=True,
                can_filter=True,
                can_join=True,
                can_group=True,
                can_aggregate=True,
            )
            for c in cols
        }
        canonical_name = "EmployeeInformation" if table_name == "employeeinformation" else "FirmContribution"
        return TablePermission(
            table_name=canonical_name,
            can_read=True,
            scope=AccessScope.ALL,
            columns=col_perms,
            predicates=[],
        )

    def _build_talent_chief_permission(self, table_name: str) -> TablePermission:
        """Construct CHTAO talent leadership TablePermission (compensation masked)."""
        cols = _EMPLOYEE_COLUMNS if table_name == "employeeinformation" else _FIRM_CONTRIBUTION_COLUMNS
        col_perms: dict[str, ColumnPermission] = {}

        for c in cols:
            is_sensitive = c.lower() in _SENSITIVE_COMPENSATION_COLUMNS
            col_perms[c.lower()] = self._col(
                name=c,
                sensitivity=ColumnSensitivity.CONFIDENTIAL if is_sensitive else ColumnSensitivity.INTERNAL,
                can_select=not is_sensitive,
                can_filter=not is_sensitive,
                can_join=True if not is_sensitive else False,
                can_group=not is_sensitive,
                can_aggregate=not is_sensitive,
            )

        canonical_name = "EmployeeInformation" if table_name == "employeeinformation" else "FirmContribution"
        return TablePermission(
            table_name=canonical_name,
            can_read=True,
            scope=AccessScope.VERTICAL,
            columns=col_perms,
            predicates=[],
        )

    def _build_self_permission(self, table_name: str, email: str) -> TablePermission:
        """Construct SELF-scoped TablePermission (sensitive compensation completely hidden)."""
        cols = _EMPLOYEE_COLUMNS if table_name == "employeeinformation" else _FIRM_CONTRIBUTION_COLUMNS
        col_perms: dict[str, ColumnPermission] = {}

        for c in cols:
            is_sensitive = c.lower() in _SENSITIVE_COMPENSATION_COLUMNS
            col_perms[c.lower()] = self._col(
                name=c,
                sensitivity=ColumnSensitivity.CONFIDENTIAL if is_sensitive else ColumnSensitivity.INTERNAL,
                # Regular employees cannot select, filter, or aggregate compensation data
                can_select=not is_sensitive,
                can_filter=not is_sensitive,
                can_join=True if not is_sensitive else False,
                can_group=not is_sensitive,
                can_aggregate=not is_sensitive,
            )

        canonical_name = "EmployeeInformation" if table_name == "employeeinformation" else "FirmContribution"
        predicate = PredicateSpec.for_self(
            column="employeeMailId",
            parameter_name="auth_user_email",
        )

        return TablePermission(
            table_name=canonical_name,
            can_read=True,
            scope=AccessScope.SELF,
            columns=col_perms,
            predicates=[predicate],
        )
