"""
Centralized exception registry for all domain, application, and platform errors.

Groups:
- Core Platform & DB: PlatformException, DatabaseUnavailableError, DevAuthDisabledError
- Authentication: AuthenticationError, MissingIdentityError, InvalidIdentityError, UserNotFoundError, NoActiveAssignmentsError
- Authorization: AuthorizationError, TableAccessDeniedError, ColumnAccessDeniedError, JoinAccessDeniedError, SqlSecurityError
- Chat & Conversation: ConversationDomainException, ChatDomainException, ConversationNotFoundError, MessageNotFoundError,
                       GenerationConflictError, GenerationFencingError, DuplicateMessageError, InvalidFeedbackError, StaleSummaryError
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
from exceptions.chat import (
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
