"""
Centralized exception package inside core for all domain, application, and platform errors.
"""
from core.exceptions.base import (
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
from core.exceptions.chat import (
    ChatDomainException,
    ConversationDomainException,
    ConversationNotFoundError,
    DuplicateMessageError,
    GenerationConflictError,
    GenerationFencingError,
    InvalidFeedbackError,
    MessageNotFoundError,
    StaleSummaryError,
)

__all__ = [
    # Core & Auth
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
    # Chat & Conversation
    "ConversationDomainException",
    "ChatDomainException",
    "ConversationNotFoundError",
    "MessageNotFoundError",
    "GenerationConflictError",
    "GenerationFencingError",
    "DuplicateMessageError",
    "InvalidFeedbackError",
    "StaleSummaryError",
]
