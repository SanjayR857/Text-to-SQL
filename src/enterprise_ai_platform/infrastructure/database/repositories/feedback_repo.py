"""
Message feedback repository implementation.

Handles feedback upserting and retrieval with composite ownership verification.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai_platform.infrastructure.database.models.chat import MessageFeedback


class FeedbackRepository:
    """Data access repository for MessageFeedback entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        message_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        rating: int,
        comment: str | None = None,
    ) -> MessageFeedback:
        """
        Create or update feedback for an assistant message.
        Guaranteed to be scoped to the conversation and user via composite foreign keys.
        """
        now = datetime.now(timezone.utc)
        insert_stmt = insert(MessageFeedback).values(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            created_at=now,
        )

        upsert_stmt = insert_stmt.on_conflict_do_update(
            constraint="uq_feedback_message_user",
            set_={
                "rating": insert_stmt.excluded.rating,
                "comment": insert_stmt.excluded.comment,
                "created_at": now,
            },
        ).returning(MessageFeedback)

        result = await self.session.execute(upsert_stmt)
        feedback = result.scalar_one()
        await self.session.refresh(feedback)
        return feedback

    async def get_by_message_and_user(
        self,
        message_id: UUID,
        user_id: UUID,
    ) -> MessageFeedback | None:
        """Fetch existing feedback submitted by a specific user for a message."""
        query = select(MessageFeedback).where(
            MessageFeedback.message_id == message_id,
            MessageFeedback.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_conversation(
        self,
        conversation_id: UUID,
    ) -> list[MessageFeedback]:
        """Fetch all feedback records for messages within a conversation."""
        query = (
            select(MessageFeedback)
            .where(MessageFeedback.conversation_id == conversation_id)
            .order_by(MessageFeedback.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
