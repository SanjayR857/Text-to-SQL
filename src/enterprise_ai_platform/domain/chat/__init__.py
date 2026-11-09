"""
Domain layer for the Chat / Conversation Management Module.
"""
from enterprise_ai_platform.domain.chat.entities import (
    ConversationEntity,
    ConversationSummaryEntity,
    MessageEntity,
    MessageFeedbackEntity,
)
from enterprise_ai_platform.domain.chat.enums import (
    ConversationStatus,
    GenerationStatus,
    MessageRole,
    MessageStatus,
    TitleSource,
)
from enterprise_ai_platform.domain.chat.exceptions import (
    ChatDomainException,
    ConversationNotFoundError,
    DuplicateMessageError,
    GenerationConflictError,
    GenerationFencingError,
    InvalidFeedbackError,
    MessageNotFoundError,
    StaleSummaryError,
)
from enterprise_ai_platform.domain.chat.protocols import (
    AIGeneratorProtocol,
    ContextMessage,
    GenerationContext,
    StreamChunk,
    SummaryGeneratorProtocol,
    TitleGeneratorProtocol,
)

__all__ = [
    # Enums
    "ConversationStatus",
    "GenerationStatus",
    "TitleSource",
    "MessageRole",
    "MessageStatus",
    # Entities
    "ConversationEntity",
    "MessageEntity",
    "MessageFeedbackEntity",
    "ConversationSummaryEntity",
    # Exceptions
    "ChatDomainException",
    "ConversationNotFoundError",
    "MessageNotFoundError",
    "GenerationConflictError",
    "GenerationFencingError",
    "DuplicateMessageError",
    "InvalidFeedbackError",
    "StaleSummaryError",
    # Protocols & Models
    "StreamChunk",
    "ContextMessage",
    "GenerationContext",
    "AIGeneratorProtocol",
    "TitleGeneratorProtocol",
    "SummaryGeneratorProtocol",
]
