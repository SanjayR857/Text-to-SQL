"""
Policy handler for Office Attendance and swipe records.
"""
from typing import Any

from enterprise_ai_platform.auth.access_context import (
    AccessScope,
    ColumnPermission,
    ColumnSensitivity,
    TablePermission,
)
from enterprise_ai_platform.auth.handlers.base_handler import (
    BasePolicyHandler,
)
from enterprise_ai_platform.auth.predicate_spec import (
    PredicateSpec,
)
from enterprise_ai_platform.auth.role import Role
from enterprise_ai_platform.auth.user import UserContext

_ATTENDANCE_COLUMNS = [
    "id",
    "employeeMailId",
    "swipeDate",
    "inTime",
    "outTime",
    "totalHours",
    "location",
    "status",
]

_ATTENDANCE_UPLOAD_COLUMNS = [
    "id",
    "fileName",
    "uploadedBy",
    "uploadedAt",
    "recordsProcessed",
    "status",
]


class AttendanceAccessHandler(BasePolicyHandler):
    """
    Enforces authorization on office attendance and badge swipes.

    - Admin / EP / CHENO Chief (Enablement Office): Full attendance oversight (ALL/VERTICAL).
    - Employee: Strictly their own daily attendance records (SELF on employeeMailId).
    - AttendanceUpload: Administrative only; hidden from employees.
    """

    SUPPORTED_TABLES = {"officeattendance", "officeattendanceupload"}

    def can_handle(self, table_name: str) -> bool:
        """Check if table is handled by AttendanceAccessHandler."""
        return table_name.strip().lower() in self.SUPPORTED_TABLES

    def resolve_table_permission(
        self,
        table_name: str,
        user_context: UserContext,
        parameters: dict[str, Any],
    ) -> TablePermission:
        """Resolve permissions for attendance tables."""
        clean_table = table_name.strip().lower()
        normalized_email = user_context.email.strip().lower()
        parameters["auth_user_email"] = normalized_email

        # 1. Admin, EP, or CHENO Chief (Enablement Office)
        is_cheno_chief = any(
            a.role == Role.CHIEF and a.vertical_code.upper() == "CHENO"
            for a in user_context.assignments
        )
        if user_context.is_ca_admin or user_context.has_role(Role.EP) or is_cheno_chief:
            cols = _ATTENDANCE_COLUMNS if clean_table == "officeattendance" else _ATTENDANCE_UPLOAD_COLUMNS
            canonical_name = "OfficeAttendance" if clean_table == "officeattendance" else "OfficeAttendanceUpload"
            col_perms = {
                c.lower(): self._col(
                    name=c,
                    sensitivity=ColumnSensitivity.INTERNAL,
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

        # 2. Upload table is forbidden for regular employees
        if clean_table == "officeattendanceupload":
            return TablePermission(
                table_name="OfficeAttendanceUpload",
                can_read=False,
                scope=AccessScope.NONE,
                columns={},
                predicates=[PredicateSpec.deny()],
            )

        # 3. Regular employee querying OfficeAttendance -> SELF scope
        col_perms = {
            c.lower(): self._col(
                name=c,
                sensitivity=ColumnSensitivity.INTERNAL,
                can_select=True,
                can_filter=True,
                can_join=True,
                can_group=True,
                can_aggregate=True,
            )
            for c in _ATTENDANCE_COLUMNS
        }
        predicate = PredicateSpec.for_self(
            column="employeeMailId",
            parameter_name="auth_user_email",
        )
        return TablePermission(
            table_name="OfficeAttendance",
            can_read=True,
            scope=AccessScope.SELF,
            columns=col_perms,
            predicates=[predicate],
        )
