"""
Domain identity module: entities, value objects, and roles.
"""
from enterprise_ai_platform.domain.identity.role import Area, Role
from enterprise_ai_platform.domain.identity.user import (
    AccessScope,
    RequestIdentity,
    RoleAssignmentContext,
    UserContext,
)

__all__ = [
    "Area",
    "Role",
    "RequestIdentity",
    "RoleAssignmentContext",
    "AccessScope",
    "UserContext",
]
