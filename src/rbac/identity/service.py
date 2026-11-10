"""
User context resolution service.

Orchestrates user identity verification, active role assignments retrieval,
and access scope calculations (verticals and lead project associations).
"""
import re

import structlog

from core.exceptions import (
    InvalidIdentityError,
    UserNotFoundError,
)
from rbac.identity.role import Area, Role
from rbac.identity.user import (
    AccessScope,
    RoleAssignmentContext,
    UserContext,
)
from rbac.identity.repository import (
    UserContextRepository,
)

logger = structlog.get_logger(__name__)

# Basic RFC 5322-compatible email check
_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserContextService:
    """
    Application service that resolves and constructs the typed UserContext for a principal.
    Enforces business rules regarding identity validation, active verticals, and lead project scopes.
    """

    def __init__(self, repository: UserContextRepository) -> None:
        """
        Initialize service with repository dependency.

        Args:
            repository: UserContextRepository instance.
        """
        self._repo = repository

    async def resolve_user_context(self, email: str) -> UserContext:
        """
        Resolve the complete UserContext for the specified user email.

        Steps:
            1. Normalize and validate email format.
            2. Resolve user UUID from PostgreSQL users table.
            3. Retrieve active role assignments joined with active verticals.
            4. Calculate access scope:
               - Vertical codes: all distinct active vertical codes assigned.
               - Project IDs: assigned active projects if user holds LEAD role;
                 empty for CHIEF (pending schema relationship) and other roles.

        Args:
            email: Corporate user email.

        Returns:
            Immutable typed UserContext object.

        Raises:
            InvalidIdentityError: If email is empty or malformed.
            UserNotFoundError: If email does not match any record in the users table.
            NoActiveAssignmentsError: If the user has no active role assignments.
            DatabaseUnavailableError: If a database connection error occurs.
        """
        if not email or not isinstance(email, str):
            raise InvalidIdentityError("Identity email must be a non-empty string.")

        clean_email = email.strip().lower()
        if not _EMAIL_REGEX.match(clean_email):
            raise InvalidIdentityError(f"Identity email '{clean_email}' is not a valid email address.")

        # 1. Resolve principal UUID from users table
        user_id = await self._repo.get_user_id_by_email(clean_email)
        if user_id is None:
            logger.warning("user_context_service.user_not_found", email=clean_email)
            raise UserNotFoundError(f"User with email '{clean_email}' does not exist.")

        # 2. Retrieve active role assignments with active verticals
        db_assignments = await self._repo.get_active_role_assignments(clean_email)

        # 3. Construct assignment contexts (empty list if no elevated roles provisioned)
        assignments: list[RoleAssignmentContext] = [
            RoleAssignmentContext(
                role=Role(raw["role"]),
                vertical_code=raw["vertical_code"].strip().upper(),
                vertical_name=raw["vertical_name"],
                vertical_area=Area(raw["vertical_area"]),
            )
            for raw in db_assignments
        ]

        # 4. Derive uppercase vertical codes
        vertical_codes = sorted({a.vertical_code for a in assignments})

        # 5. Derive project scope: only query ProjectName if user holds at least one LEAD role
        has_lead_role = any(a.role == Role.LEAD for a in assignments)
        project_ids: list[str] = []
        if has_lead_role:
            project_ids = await self._repo.get_assigned_lead_project_ids(clean_email)
            project_ids.sort()

        logger.info(
            "user_context_service.resolved",
            user_id=str(user_id),
            email=clean_email,
            is_unassigned=len(assignments) == 0,
            roles=[a.role.value for a in assignments],
            verticals=vertical_codes,
            lead_projects_count=len(project_ids),
        )

        return UserContext(
            user_id=user_id,
            email=clean_email,
            assignments=assignments,
            access_scope=AccessScope(
                vertical_codes=vertical_codes,
                project_ids=project_ids,
            ),
        )
