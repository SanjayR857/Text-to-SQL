"""
SQLAlchemy 2.x Declarative ORM models for all database tables across the platform.

Centralized registry providing direct access to Base and all table models:
- User (platform identity)
- Conversation, Message, MessageFeedback, ConversationSummary (chat & dialogue)
- SchemaEmbeddingModel, EntityEmbeddingModel (pgvector search & retrieval)
"""
from core.database import Base
from models.user import User
from models.chat import (
    Conversation,
    ConversationSummary,
    Message,
    MessageFeedback,
)
from models.text_to_sql import (
    EntityEmbeddingModel,
    SchemaEmbeddingModel,
)

__all__ = [
    "Base",
    "User",
    "Conversation",
    "Message",
    "MessageFeedback",
    "ConversationSummary",
    "SchemaEmbeddingModel",
    "EntityEmbeddingModel",
]
