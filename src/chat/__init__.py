"""
Chat & conversation management: models, repositories, lifecycle services, and SSE streaming.
"""
from chat.conversation import (
    ConversationEntity,
    ConversationStatus,
    ConversationSummaryEntity,
    GenerationStatus,
    TitleSource,
)
from chat.exceptions import (
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
from chat.message import (
    MessageEntity,
    MessageFeedbackEntity,
    MessageRole,
    MessageStatus,
)
from chat.mock_ai_generator import MockAIGenerator
from chat.models import (
    Conversation,
    ConversationSummary,
    Message,
    MessageFeedback,
)
from chat.protocols import (
    AIGeneratorProtocol,
    ContextMessage,
    GenerationContext,
    StreamChunk,
    SummaryGeneratorProtocol,
    TitleGeneratorProtocol,
)
from chat.repositories import (
    ConversationRepository,
    FeedbackRepository,
    MessageRepository,
    SummaryRepository,
)
from chat.sse_formatter import SSEFormatter


def __getattr__(name: str):
    """Lazy export of conversation services to avoid circular imports."""
    if name in {
        "ConversationService",
        "MessageService",
        "FeedbackService",
        "ContextService",
        "StreamingOrchestrator",
    }:
        import services.conversation as sc

        return getattr(sc, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ConversationEntity",
    "ConversationSummaryEntity",
    "ConversationStatus",
    "GenerationStatus",
    "TitleSource",
    "MessageEntity",
    "MessageFeedbackEntity",
    "MessageRole",
    "MessageStatus",
    "Conversation",
    "Message",
    "MessageFeedback",
    "ConversationSummary",
    "ConversationRepository",
    "MessageRepository",
    "FeedbackRepository",
    "SummaryRepository",
    "ConversationService",
    "MessageService",
    "FeedbackService",
    "ContextService",
    "StreamingOrchestrator",
    "SSEFormatter",
    "MockAIGenerator",
    "AIGeneratorProtocol",
    "TitleGeneratorProtocol",
    "SummaryGeneratorProtocol",
    "ContextMessage",
    "GenerationContext",
    "StreamChunk",
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
