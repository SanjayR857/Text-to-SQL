"""
Pydantic schemas for authentication and user-context responses.
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai_platform.domain.identity.user import AccessScope, RoleAssignmentContext


class UserContextResponse(BaseModel):
    """
    Public response representation of the resolved authenticated user context.
    Exposes only approved context fields to client callers.
    """

    model_config = ConfigDict(frozen=True)

    user_id: UUID = Field(..., description="Platform user UUID")
    email: str = Field(..., description="Corporate user email")
    assignments: list[RoleAssignmentContext] = Field(
        default_factory=list,
        description="Active vertical role assignments",
    )
    access_scope: AccessScope = Field(
        default_factory=AccessScope,
        description="Effective vertical and project access scope",
    )
