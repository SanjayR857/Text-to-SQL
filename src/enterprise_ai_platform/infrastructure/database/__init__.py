"""
Database infrastructure package: models, engine lifecycle, session management, and repositories.
"""
from enterprise_ai_platform.infrastructure.database.base import Base
from enterprise_ai_platform.infrastructure.database.connection_manager import (
    check_connection,
    close_engine,
    get_async_engine,
)
from enterprise_ai_platform.infrastructure.database.models import (
    Conversation,
    ConversationSummary,
    EntityEmbeddingModel,
    Message,
    MessageFeedback,
    SchemaEmbeddingModel,
    User,
)
from enterprise_ai_platform.infrastructure.database.schema_introspector import (
    PostgresSchemaIntrospector,
)
from enterprise_ai_platform.infrastructure.database.session import (
    async_db_session,
    get_db_session,
    get_session_factory,
)

__all__ = [
    "Base",
    "User",
    "Conversation",
    "Message",
    "MessageFeedback",
    "ConversationSummary",
    "EntityEmbeddingModel",
    "get_async_engine",
    "close_engine",
    "check_connection",
    "get_session_factory",
    "get_db_session",
    "async_db_session",
    "PostgresSchemaIntrospector",
    "SchemaEmbeddingModel",
]
