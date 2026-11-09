"""
Message repository implementation.

Handles message ingestion, cursor history retrieval, context assembly querying,
and fenced completion/interruption/failure updates.
"""
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai_platform.infrastructure.database.models.conversation import Message


class MessageRepository:
    """Data access repository for Message entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_client_message_id(
        self,
        conversation_id: UUID,
        client_message_id: UUID,
    ) -> Message | None:
        """
        Lookup an existing user message by idempotency token.
        Used to prevent duplicate processing of retried POST submissions.
        """
        query = select(Message).where(
            Message.conversation_id == conversation_id,
            Message.client_message_id == client_message_id,
            Message.role == "user",
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        message_id: UUID,
        conversation_id: UUID,
    ) -> Message | None:
        """Fetch a single message by ID within a conversation."""
        query = select(Message).where(
            Message.id == message_id,
            Message.conversation_id == conversation_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_user_and_assistant_messages(
        self,
        conversation_id: UUID,
        user_sequence: int,
        user_content: str,
        assistant_message_id: UUID,
        assistant_sequence: int,
        client_message_id: UUID | None = None,
        parent_message_id: UUID | None = None,
    ) -> tuple[Message, Message]:
        """
        Persist the completed user prompt and the pending assistant placeholder
        in sequence order within the same transaction.
        """
        user_msg = Message(
            conversation_id=conversation_id,
            sequence_number=user_sequence,
            role="user",
            content=user_content,
            status="completed",
            client_message_id=client_message_id,
            parent_message_id=parent_message_id,
            metadata_={},
        )
        assistant_msg = Message(
            id=assistant_message_id,
            conversation_id=conversation_id,
            sequence_number=assistant_sequence,
            role="assistant",
            content="",
            status="pending",
            client_message_id=None,
            parent_message_id=user_msg.id,
            metadata_={},
        )

        self.session.add(user_msg)
        await self.session.flush()

        assistant_msg.parent_message_id = user_msg.id
        self.session.add(assistant_msg)
        await self.session.flush()

        return user_msg, assistant_msg

    async def get_history_cursor(
        self,
        conversation_id: UUID,
        cursor_sequence: int | None = None,
        limit: int = 50,
    ) -> list[Message]:
        """
        Retrieve messages in chronological sequence order with cursor pagination.
        If cursor_sequence is provided, returns messages with sequence_number > cursor_sequence.
        """
        query = select(Message).where(Message.conversation_id == conversation_id)
        if cursor_sequence is not None:
            query = query.where(Message.sequence_number > cursor_sequence)

        query = query.order_by(Message.sequence_number.asc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_prior_context_messages(
        self,
        conversation_id: UUID,
        max_sequence: int,
        limit: int = 50,
    ) -> list[Message]:
        """
        Fetch prior historical messages up to max_sequence (excluding the current prompt)
        for external generation context assembly.
        """
        query = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.sequence_number <= max_sequence,
                Message.status == "completed",
            )
            .order_by(desc(Message.sequence_number))
            .limit(limit)
        )
        result = await self.session.execute(query)
        messages = list(result.scalars().all())
        # Return in ascending chronological order
        messages.reverse()
        return messages

    async def fenced_complete_message(
        self,
        assistant_message_id: UUID,
        conversation_id: UUID,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Fenced persistence of completed assistant response.
        Only succeeds if the message is currently in 'pending' or 'streaming' state.
        Returns True if row was updated (fencing verified), False otherwise.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Message)
            .where(
                Message.id == assistant_message_id,
                Message.conversation_id == conversation_id,
                Message.status.in_(["pending", "streaming"]),
            )
            .values(
                content=content,
                status="completed",
                completed_at=now,
                metadata_=metadata or {},
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount == 1

    async def fenced_interrupt_message(
        self,
        assistant_message_id: UUID,
        conversation_id: UUID,
        partial_content: str,
        reason: str = "client_disconnect",
    ) -> bool:
        """
        Fenced persistence of interrupted assistant response saving partial tokens.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Message)
            .where(
                Message.id == assistant_message_id,
                Message.conversation_id == conversation_id,
                Message.status.in_(["pending", "streaming"]),
            )
            .values(
                content=partial_content,
                status="interrupted",
                completed_at=now,
                metadata_=Message.metadata_.concat(
                    func.jsonb_build_object("interrupted_reason", reason)
                ),
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount == 1

    async def fenced_fail_message(
        self,
        assistant_message_id: UUID,
        conversation_id: UUID,
        error_detail: str,
    ) -> bool:
        """
        Fenced persistence of failed assistant response saving error details.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Message)
            .where(
                Message.id == assistant_message_id,
                Message.conversation_id == conversation_id,
                Message.status.in_(["pending", "streaming"]),
            )
            .values(
                status="failed",
                completed_at=now,
                metadata_=Message.metadata_.concat(
                    func.jsonb_build_object("error", error_detail)
                ),
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount == 1
