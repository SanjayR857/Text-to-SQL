"""
Conversation domain package: entities, value objects, exceptions, and protocols.
"""
from enterprise_ai_platform.domain.conversations.conversation import (
    ConversationEntity,
    ConversationStatus,
    ConversationSummaryEntity,
    GenerationStatus,
    TitleSource,
)
from enterprise_ai_platform.domain.conversations.exceptions import (
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
from enterprise_ai_platform.domain.conversations.message import (
    MessageEntity,
    MessageFeedbackEntity,
    MessageRole,
    MessageStatus,
)
from enterprise_ai_platform.domain.conversations.protocols import (
    AIGeneratorProtocol,
    ContextMessage,
    GenerationContext,
    StreamChunk,
    SummaryGeneratorProtocol,
    TitleGeneratorProtocol,
)

__all__ = [
    # Entities
    "ConversationEntity",
    "ConversationSummaryEntity",
    "MessageEntity",
    "MessageFeedbackEntity",
    # Enums
    "ConversationStatus",
    "GenerationStatus",
    "TitleSource",
    "MessageRole",
    "MessageStatus",
    # Exceptions
    "ConversationDomainException",
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
