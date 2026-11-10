"""
Policy handler for qualitative rating comments and evaluation feedback.
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
    PredicateSpec,
)
from auth.role import Role
from auth.user import UserContext

_RATING_COMMENT_COLUMNS = [
    "id",
    "module",
    "rateeEmail",
    "appraisalYearId",
    "quarter",
    "contextKey",
    "comment",
    "createdBy",
]


class RatingCommentAccessHandler(BasePolicyHandler):
    """
    Enforces authorization on qualitative rating feedback.

    - Admin / EP: Full access across enterprise (ALL).
    - Employee: Only comments directed to the employee (SELF on rateeEmail).
    """

    SUPPORTED_TABLES = {"ratingcomment"}

    def can_handle(self, table_name: str) -> bool:
        """Check if table is handled by RatingCommentAccessHandler."""
        return table_name.strip().lower() in self.SUPPORTED_TABLES

    def resolve_table_permission(
        self,
        table_name: str,
        user_context: UserContext,
        parameters: dict[str, Any],
    ) -> TablePermission:
        """Resolve permissions for the RatingComment table."""
        normalized_email = user_context.email.strip().lower()
        parameters["auth_user_email"] = normalized_email

        # 1. Admin or EP
        if user_context.is_ca_admin or user_context.has_role(Role.EP):
            col_perms = {
                c.lower(): self._col(
                    name=c,
                    sensitivity=ColumnSensitivity.RESTRICTED,
                    can_select=True,
                    can_filter=True,
                    can_join=True,
                    can_group=True,
                    can_aggregate=True,
                )
                for c in _RATING_COMMENT_COLUMNS
            }
            return TablePermission(
                table_name="RatingComment",
                can_read=True,
                scope=AccessScope.ALL,
                columns=col_perms,
                predicates=[],
            )

        # 2. Regular employee can only see their own feedback
        predicate = PredicateSpec.for_self(
            column="rateeEmail",
            parameter_name="auth_user_email",
        )
        col_perms = {
            c.lower(): self._col(
                name=c,
                sensitivity=ColumnSensitivity.RESTRICTED,
                can_select=True,
                can_filter=True,
                can_join=True,
                can_group=False,
                can_aggregate=False,
            )
            for c in _RATING_COMMENT_COLUMNS
        }
        return TablePermission(
            table_name="RatingComment",
            can_read=True,
            scope=AccessScope.SELF,
            columns=col_perms,
            predicates=[predicate],
        )
