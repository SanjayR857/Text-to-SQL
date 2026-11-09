"""
Conversation service.

Coordinates conversation lifecycle, metadata updates, cursor-based pagination,
and soft deletion.
"""
from datetime import datetime
from uuid import UUID

from enterprise_ai_platform.domain.conversations.exceptions import ConversationNotFoundError
from enterprise_ai_platform.infrastructure.database.models.chat import Conversation
from enterprise_ai_platform.infrastructure.database.repositories.conversation_repo import (
    ConversationRepository,
)


class ConversationService:
    """Service governing conversation lifecycle business operations."""

    def __init__(self, conversation_repo: ConversationRepository) -> None:
        self.conversation_repo = conversation_repo

    async def create_conversation(
        self,
        user_id: UUID,
        title: str | None = None,
    ) -> Conversation:
        """
        Create a new conversation for the authenticated user.
        If title is provided, mark title_source as 'user'; otherwise 'default'.
        """
        effective_title = title.strip() if title and title.strip() else "New Conversation"
        title_source = "user" if (title and title.strip()) else "default"

        return await self.conversation_repo.create(
            user_id=user_id,
            title=effective_title,
            title_source=title_source,
        )

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        """
        Fetch a conversation owned by the authenticated user.
        Raises ConversationNotFoundError if deleted or not owned by user.
        """
        conversation = await self.conversation_repo.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return conversation

    async def list_conversations(
        self,
        user_id: UUID,
        cursor_last_message_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 20,
    ) -> list[Conversation]:
        """
        List active conversations owned by the user using cursor pagination.
        """
        bounded_limit = min(max(1, limit), 100)
        return await self.conversation_repo.list_paginated(
            user_id=user_id,
            cursor_last_message_at=cursor_last_message_at,
            cursor_id=cursor_id,
            limit=bounded_limit,
        )

    async def update_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
        title: str | None = None,
        is_pinned: bool | None = None,
        status: str | None = None,
    ) -> Conversation:
        """
        Update mutable conversation attributes.
        Setting a custom title permanently marks title_source as 'user'.
        """
        title_clean = title.strip() if title is not None else None
        title_source = "user" if title_clean is not None else None

        updated = await self.conversation_repo.update_metadata(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title_clean,
            title_source=title_source,
            is_pinned=is_pinned,
            status=status,
        )
        if updated is None:
            raise ConversationNotFoundError(conversation_id)
        return updated

    async def soft_delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Soft-delete a conversation, hiding it from standard queries.
        """
        success = await self.conversation_repo.soft_delete(conversation_id, user_id)
        if not success:
            raise ConversationNotFoundError(conversation_id)
