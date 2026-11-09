"""
Conversation summary repository implementation.

Handles retrieving the active summary and serialized monotonic progression
of conversation summaries with conversation-level locking.
"""
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai_platform.infrastructure.database.models.conversation import (
    Conversation,
    ConversationSummary,
)


class SummaryRepository:
    """Data access repository for ConversationSummary entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest(self, conversation_id: UUID) -> ConversationSummary | None:
        """Fetch the most recent summary version for a conversation."""
        query = (
            select(ConversationSummary)
            .where(ConversationSummary.conversation_id == conversation_id)
            .order_by(desc(ConversationSummary.version))
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_next_version(
        self,
        conversation_id: UUID,
        summary_text: str,
        summarized_through_sequence: int,
    ) -> ConversationSummary | None:
        """
        Atomically persist a new summary version while enforcing monotonic progression.

        1. Locks the conversation row via SELECT ... FOR UPDATE to serialize summary writers.
        2. Inspects the latest committed summary version and watermark sequence boundary.
        3. Only inserts if summarized_through_sequence > latest.summarized_through_sequence.
        4. If an out-of-order task completes with an older boundary, discards it (returns None).
        """
        # Step 1: Serialize summary progression for this conversation
        lock_query = (
            select(Conversation.id)
            .where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
            .with_for_update()
        )
        lock_res = await self.session.execute(lock_query)
        if lock_res.scalar_one_or_none() is None:
            return None

        # Step 2: Read current latest summary
        latest = await self.get_latest(conversation_id)

        # Step 3: Verify strict monotonic boundary progression
        if latest is not None and summarized_through_sequence <= latest.summarized_through_sequence:
            # Outdated summary worker finished out of order; safely discard
            return None

        next_version = (latest.version + 1) if latest is not None else 1

        # Step 4: Persist new version
        new_summary = ConversationSummary(
            conversation_id=conversation_id,
            summary=summary_text,
            version=next_version,
            summarized_through_sequence=summarized_through_sequence,
        )
        self.session.add(new_summary)
        await self.session.flush()
        return new_summary
