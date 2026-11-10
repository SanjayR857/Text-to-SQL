"""
Chat & conversation management: models, repositories, lifecycle services, and SSE streaming.
"""
from enterprise_ai_platform.chat.context_service import ContextService
from enterprise_ai_platform.chat.conversation import (
    ConversationEntity,
    ConversationStatus,
    ConversationSummaryEntity,
    GenerationStatus,
    TitleSource,
)
from enterprise_ai_platform.chat.exceptions import (
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
from enterprise_ai_platform.chat.feedback_service import FeedbackService
from enterprise_ai_platform.chat.message import (
    MessageEntity,
    MessageFeedbackEntity,
    MessageRole,
    MessageStatus,
)
from enterprise_ai_platform.chat.message_service import MessageService
from enterprise_ai_platform.chat.mock_ai_generator import MockAIGenerator
from enterprise_ai_platform.chat.models import (
    Conversation,
    ConversationSummary,
    Message,
    MessageFeedback,
)
from enterprise_ai_platform.chat.protocols import (
    AIGeneratorProtocol,
    ContextMessage,
    GenerationContext,
    StreamChunk,
    SummaryGeneratorProtocol,
    TitleGeneratorProtocol,
)
from enterprise_ai_platform.chat.repositories import (
    ConversationRepository,
    FeedbackRepository,
    MessageRepository,
    SummaryRepository,
)
from enterprise_ai_platform.chat.service import ConversationService
from enterprise_ai_platform.chat.sse_formatter import SSEFormatter
from enterprise_ai_platform.chat.streaming_orchestrator import StreamingOrchestrator

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
