"""
Chat & conversation management: models, repositories, lifecycle services, and SSE streaming.
"""
from chat.context_service import ContextService
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
from chat.feedback_service import FeedbackService
from chat.message import (
    MessageEntity,
    MessageFeedbackEntity,
    MessageRole,
    MessageStatus,
)
from chat.message_service import MessageService
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
from chat.service import ConversationService
from chat.sse_formatter import SSEFormatter
from chat.streaming_orchestrator import StreamingOrchestrator

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
