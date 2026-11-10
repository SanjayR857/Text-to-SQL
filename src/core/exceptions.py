"""
Domain and application exception hierarchy for the platform.
"""


class PlatformException(Exception):
    """Base exception for all platform domain and application errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthenticationError(PlatformException):
    """Base exception for authentication failures resulting in HTTP 401 Unauthorized."""


class MissingIdentityError(AuthenticationError):
    """Raised when an identity header or credential is missing."""


class InvalidIdentityError(AuthenticationError):
    """Raised when an identity header or email format is malformed."""


class DevAuthDisabledError(PlatformException):
    """Raised when development authentication is disabled or attempted in production."""


class UserNotFoundError(PlatformException):
    """Raised when an authenticated user email is not found in the platform users table."""


class NoActiveAssignmentsError(PlatformException):
    """Raised when a user exists but has no active role or vertical assignments."""


class DatabaseUnavailableError(PlatformException):
    """Raised when database connection or execution fails."""


class AuthorizationError(PlatformException):
    """Base exception for authorization and access control violations."""


class TableAccessDeniedError(AuthorizationError):
    """Raised when an unauthorized table is referenced in a query."""


class ColumnAccessDeniedError(AuthorizationError):
    """Raised when an unauthorized column or operation (select, filter, group, aggregate) is attempted."""


class JoinAccessDeniedError(AuthorizationError):
    """Raised when an unauthorized or unapproved join relationship is detected."""


class SqlSecurityError(AuthorizationError):
    """Raised when SQL AST validation detects forbidden statements, functions, or patterns."""

