"""
Authorization, RBAC, User Context, and Join Validation services.
"""
from enterprise_ai_platform.auth.access_context import (
    AccessScope,
    ColumnPermission,
    ColumnSensitivity,
    ResolvedAccessContext,
    TablePermission,
)
from enterprise_ai_platform.auth.handlers.attendance_handler import AttendanceAccessHandler
from enterprise_ai_platform.auth.handlers.base_handler import BasePolicyHandler
from enterprise_ai_platform.auth.handlers.demand_handler import DemandAccessHandler
from enterprise_ai_platform.auth.handlers.employee_handler import EmployeeAccessHandler
from enterprise_ai_platform.auth.handlers.project_handler import ProjectAccessHandler
from enterprise_ai_platform.auth.handlers.rating_comment_handler import RatingCommentAccessHandler
from enterprise_ai_platform.auth.handlers.scoreboard_handler import ScoreboardAccessHandler
from enterprise_ai_platform.auth.handlers.standard_vertical_handler import StandardVerticalAccessHandler
from enterprise_ai_platform.auth.join_validation import (
    ENTERPRISE_APPROVED_JOINS,
    ApprovedJoinEdge,
    JoinGraphValidator,
)
from enterprise_ai_platform.auth.models import User
from enterprise_ai_platform.auth.policy_resolver import PolicyResolver
from enterprise_ai_platform.auth.predicate_spec import PredicateOperator, PredicateSpec
from enterprise_ai_platform.auth.repository import UserContextRepository
from enterprise_ai_platform.auth.role import Area, Role
from enterprise_ai_platform.auth.user import (
    AccessScope as UserAccessScope,
    RequestIdentity,
    RoleAssignmentContext,
    UserContext,
)
from enterprise_ai_platform.auth.user_context_service import UserContextService

__all__ = [
    "AccessScope",
    "UserAccessScope",
    "ApprovedJoinEdge",
    "AttendanceAccessHandler",
    "BasePolicyHandler",
    "ColumnPermission",
    "ColumnSensitivity",
    "DemandAccessHandler",
    "ENTERPRISE_APPROVED_JOINS",
    "EmployeeAccessHandler",
    "JoinGraphValidator",
    "PolicyResolver",
    "PredicateOperator",
    "PredicateSpec",
    "ProjectAccessHandler",
    "RatingCommentAccessHandler",
    "ResolvedAccessContext",
    "ScoreboardAccessHandler",
    "StandardVerticalAccessHandler",
    "TablePermission",
    "UserContextService",
    "Role",
    "Area",
    "UserContext",
    "RequestIdentity",
    "RoleAssignmentContext",
    "User",
    "UserContextRepository",
]
