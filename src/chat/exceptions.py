"""
Domain exceptions for the Conversation Management Module.
Re-exported from core.exceptions.chat.
"""
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
