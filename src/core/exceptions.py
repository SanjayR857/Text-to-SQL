"""
Domain and application exception hierarchy for the platform.
Re-exported from centralized exceptions module.
"""
from exceptions.core import (
    AuthenticationError,
    AuthorizationError,
    ColumnAccessDeniedError,
    DatabaseUnavailableError,
    DevAuthDisabledError,
    InvalidIdentityError,
    JoinAccessDeniedError,
    MissingIdentityError,
    NoActiveAssignmentsError,
    PlatformException,
    SqlSecurityError,
    TableAccessDeniedError,
    UserNotFoundError,
)

__all__ = [
    "PlatformException",
    "AuthenticationError",
    "MissingIdentityError",
    "InvalidIdentityError",
    "DevAuthDisabledError",
    "UserNotFoundError",
    "NoActiveAssignmentsError",
    "DatabaseUnavailableError",
    "AuthorizationError",
    "TableAccessDeniedError",
    "ColumnAccessDeniedError",
    "JoinAccessDeniedError",
    "SqlSecurityError",
]
