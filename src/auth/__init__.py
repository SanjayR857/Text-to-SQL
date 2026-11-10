"""
Authorization, RBAC, User Context, and Join Validation services.
"""
from auth.access_context import (
    AccessScope,
    ColumnPermission,
    ColumnSensitivity,
    ResolvedAccessContext,
    TablePermission,
)
from auth.handlers.attendance_handler import AttendanceAccessHandler
from auth.handlers.base_handler import BasePolicyHandler
from auth.handlers.demand_handler import DemandAccessHandler
from auth.handlers.employee_handler import EmployeeAccessHandler
from auth.handlers.project_handler import ProjectAccessHandler
from auth.handlers.rating_comment_handler import RatingCommentAccessHandler
from auth.handlers.scoreboard_handler import ScoreboardAccessHandler
from auth.handlers.standard_vertical_handler import StandardVerticalAccessHandler
from auth.join_validation import (
    ENTERPRISE_APPROVED_JOINS,
    ApprovedJoinEdge,
    JoinGraphValidator,
)
from auth.models import User
from auth.policy_resolver import PolicyResolver
from auth.predicate_spec import PredicateOperator, PredicateSpec
from auth.repository import UserContextRepository
from auth.role import Area, Role
from auth.user import (
    AccessScope as UserAccessScope,
    RequestIdentity,
    RoleAssignmentContext,
    UserContext,
)
from auth.user_context_service import UserContextService

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
