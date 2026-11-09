"""
User context repository for fetching user identities, role assignments, and lead projects.
Executes parameterized SQL queries against existing PostgreSQL tables.
"""
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai_platform.core.exceptions import DatabaseUnavailableError

logger = structlog.get_logger(__name__)


class UserContextRepository:
    """
    Data access repository for user identity and RBAC context resolution.
    Encapsulates all PostgreSQL queries and joins for the authentication layer.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with an active AsyncSession.

        Args:
            session: SQLAlchemy AsyncSession.
        """
        self._session = session

    async def get_user_id_by_email(self, email: str) -> UUID | None:
        """
        Retrieve platform user UUID by normalized email from the users table.

        Args:
            email: Canonical lowercase user email.

        Returns:
            UUID of the user if found, None otherwise.

        Raises:
            DatabaseUnavailableError: If a database error occurs.
        """
        stmt = text('SELECT id FROM users WHERE LOWER(email) = :email LIMIT 1')
        try:
            result = await self._session.execute(stmt, {"email": email.lower()})
            row = result.fetchone()
            if row and row[0]:
                val = row[0]
                return UUID(str(val)) if not isinstance(val, UUID) else val
            return None
        except SQLAlchemyError as err:
            logger.error(
                "user_context_repo.get_user_id_failed",
                email=email,
                error=str(err),
            )
            raise DatabaseUnavailableError("Failed to query user identity from database.") from err

    async def get_active_role_assignments(self, email: str) -> list[dict[str, Any]]:
        """
        Retrieve active role assignments joined with active verticals for the specified email.
        Inactive verticals are excluded.

        Args:
            email: Canonical lowercase user email.

        Returns:
            List of dictionaries containing role, vertical_code, vertical_name, and vertical_area.

        Raises:
            DatabaseUnavailableError: If a database error occurs.
        """
        stmt = text('''
            SELECT r.role, v.code AS vertical_code, v.name AS vertical_name, v.area AS vertical_area
            FROM "RoleAssignment" r
            JOIN "Vertical" v ON r."verticalCode" = v.code
            WHERE LOWER(r.email) = :email AND v."isActive" = TRUE
        ''')
        try:
            result = await self._session.execute(stmt, {"email": email.lower()})
            return [dict(r._mapping) for r in result.fetchall()]
        except SQLAlchemyError as err:
            logger.error(
                "user_context_repo.get_role_assignments_failed",
                email=email,
                error=str(err),
            )
            raise DatabaseUnavailableError("Failed to query role assignments from database.") from err

    async def get_assigned_lead_project_ids(self, email: str) -> list[str]:
        """
        Retrieve active project IDs where the given email is listed in teamLeadMails.

        Args:
            email: Canonical lowercase user email.

        Returns:
            List of project ID strings.

        Raises:
            DatabaseUnavailableError: If a database error occurs.
        """
        stmt = text('''
            SELECT id
            FROM "ProjectName"
            WHERE status = 'Active' AND :email = ANY("teamLeadMails")
        ''')
        try:
            result = await self._session.execute(stmt, {"email": email.lower()})
            return [str(row[0]) for row in result.fetchall()]
        except SQLAlchemyError as err:
            logger.error(
                "user_context_repo.get_lead_projects_failed",
                email=email,
                error=str(err),
            )
            raise DatabaseUnavailableError("Failed to query lead projects from database.") from err
