"""
Message service.

Coordinates message history retrieval, message lookups, and ownership validation.
"""
from uuid import UUID

from enterprise_ai_platform.domain.conversations.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
)
from enterprise_ai_platform.infrastructure.database.models.conversation import Message
from enterprise_ai_platform.infrastructure.database.repositories.conversation_repo import (
    ConversationRepository,
)
from enterprise_ai_platform.infrastructure.database.repositories.message_repo import (
    MessageRepository,
)


class MessageService:
    """Service governing message queries and ownership verification."""

    def __init__(
        self,
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository,
    ) -> None:
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo

    async def get_conversation_history(
        self,
        conversation_id: UUID,
        user_id: UUID,
        cursor_sequence: int | None = None,
        limit: int = 50,
    ) -> list[Message]:
        """
        Fetch chronological message history for a conversation using cursor pagination.
        Verifies that the conversation belongs to the requesting user.
        """
        conversation = await self.conversation_repo.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)

        bounded_limit = min(max(1, limit), 200)
        return await self.message_repo.get_history_cursor(
            conversation_id=conversation_id,
            cursor_sequence=cursor_sequence,
            limit=bounded_limit,
        )

    async def get_message(
        self,
        conversation_id: UUID,
        message_id: UUID,
        user_id: UUID,
    ) -> Message:
        """
        Retrieve a single message by ID, validating conversation ownership.
        """
        conversation = await self.conversation_repo.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)

        message = await self.message_repo.get_by_id(message_id, conversation_id)
        if message is None:
            raise MessageNotFoundError(message_id)
        return message
