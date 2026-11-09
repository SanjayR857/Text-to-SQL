"""
Backwards-compatibility re-export for conversation database models.
"""
from enterprise_ai_platform.infrastructure.database.models.conversation import (
    Conversation,
    ConversationSummary,
    Message,
    MessageFeedback,
)

__all__ = [
    "Conversation",
    "ConversationSummary",
    "Message",
    "MessageFeedback",
]
