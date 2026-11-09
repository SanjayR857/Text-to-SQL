"""
User entity, request identity, and resolved context models.
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai_platform.domain.identity.role import Area, Role


class RequestIdentity(BaseModel):
    """
    Caller identity established during initial request authentication.
    """

    model_config = ConfigDict(frozen=True)

    email: str = Field(..., description="Canonical lowercase email address of the caller")
    auth_method: str = Field(
        default="dev_header",
        description="Mechanism used to establish identity (e.g., 'dev_header', 'entra_id_jwt')",
    )


class RoleAssignmentContext(BaseModel):
    """
    Resolved role assignment bound to a specific business vertical.
    """

    model_config = ConfigDict(frozen=True)

    role: Role = Field(..., description="Assigned organizational role")
    vertical_code: str = Field(..., description="Vertical code, e.g., CHAIO, CHDLO")
    vertical_name: str = Field(..., description="Human-readable vertical name")
    vertical_area: Area = Field(..., description="Organizational grouping (CentralApplication or IndividualModule)")


class AccessScope(BaseModel):
    """
    Resolved authorization boundaries for the authenticated principal.
    Separates assigned roles from calculated data access scope.
    """

    model_config = ConfigDict(frozen=True)

    vertical_codes: list[str] = Field(
        default_factory=list,
        description="Authorized vertical codes for schema and data scoping",
    )
    project_ids: list[str] = Field(
        default_factory=list,
        description="Authorized project UUIDs/IDs for project-level data access",
    )


class UserContext(BaseModel):
    """
    Immutable typed context of an authenticated and resolved platform user.
    Carried in request.state for downstream authorization and audit logging.
    """

    model_config = ConfigDict(frozen=True)

    user_id: UUID = Field(..., description="Platform principal UUID from users table")
    email: str = Field(..., description="Canonical lowercase user email")
    assignments: list[RoleAssignmentContext] = Field(
        default_factory=list,
        description="Active vertical role assignments",
    )
    access_scope: AccessScope = Field(
        default_factory=AccessScope,
        description="Calculated vertical and project access boundaries",
    )

    def has_role(self, role: Role) -> bool:
        """Check if user has a specific role in any active vertical."""
        return any(assignment.role == role for assignment in self.assignments)

    def has_vertical(self, vertical_code: str) -> bool:
        """Check if user has an active assignment in the given vertical."""
        return vertical_code.upper() in (v.upper() for v in self.access_scope.vertical_codes)
