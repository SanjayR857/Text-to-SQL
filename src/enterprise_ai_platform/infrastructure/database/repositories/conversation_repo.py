"""
Conversation repository implementation.

Handles conversation CRUD, ownership filtering, atomic turn sequence reservation,
generation lock release, and soft deletion.
"""
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, nulls_last, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai_platform.infrastructure.database.models.conversation import Conversation, Message


class ConversationRepository:
    """Data access repository for Conversation entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: UUID,
        title: str = "New Conversation",
        title_source: str = "default",
    ) -> Conversation:
        """Create and persist a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=title,
            title_source=title_source,
            status="active",
            is_pinned=False,
            generation_status="idle",
            next_sequence_number=1,
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_by_id(self, conversation_id: UUID, user_id: UUID) -> Conversation | None:
        """
        Fetch a single active conversation by ID and user ownership.
        Returns None if deleted or not owned by user.
        """
        query = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        user_id: UUID,
        cursor_last_message_at: datetime | None = None,
        cursor_id: UUID | None = None,
        limit: int = 20,
    ) -> list[Conversation]:
        """
        List active conversations belonging to the user, paginated via cursor.
        Ordered by: is_pinned DESC, last_message_at DESC NULLS LAST, id DESC.
        """
        query = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )

        if cursor_id is not None:
            # Cursor pagination predicate
            if cursor_last_message_at is not None:
                query = query.where(
                    (Conversation.last_message_at < cursor_last_message_at)
                    | (
                        (Conversation.last_message_at == cursor_last_message_at)
                        & (Conversation.id < cursor_id)
                    )
                    | (Conversation.last_message_at.is_(None))
                )
            else:
                query = query.where(
                    Conversation.last_message_at.is_(None),
                    Conversation.id < cursor_id,
                )

        query = query.order_by(
            desc(Conversation.is_pinned),
            nulls_last(desc(Conversation.last_message_at)),
            desc(Conversation.id),
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_metadata(
        self,
        conversation_id: UUID,
        user_id: UUID,
        title: str | None = None,
        title_source: str | None = None,
        is_pinned: bool | None = None,
        status: str | None = None,
    ) -> Conversation | None:
        """
        Update mutable conversation metadata (title, pinned status, archive status).
        Returns the updated conversation or None if not found/unauthorized.
        """
        conversation = await self.get_by_id(conversation_id, user_id)
        if conversation is None:
            return None

        if title is not None:
            conversation.title = title
            conversation.title_source = title_source or "user"
        if is_pinned is not None:
            conversation.is_pinned = is_pinned
        if status is not None:
            conversation.status = status

        conversation.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return conversation

    async def soft_delete(self, conversation_id: UUID, user_id: UUID) -> bool:
        """
        Soft-delete a conversation by setting deleted_at timestamp.
        Returns True if row was updated, False otherwise.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .values(deleted_at=now, updated_at=now)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def atomic_reserve_turn(
        self,
        conversation_id: UUID,
        user_id: UUID,
        assistant_message_id: UUID,
    ) -> tuple[int, int] | None:
        """
        Atomically reserve the next two sequence numbers and acquire generation lock.

        Sets:
          next_sequence_number = next_sequence_number + 2
          generation_status = 'generating'
          active_generation_message_id = assistant_message_id

        Returns:
          (user_sequence, assistant_sequence) if acquired, None if locked or unavailable.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.status == "active",
                Conversation.generation_status == "idle",
                Conversation.deleted_at.is_(None),
            )
            .values(
                next_sequence_number=Conversation.next_sequence_number + 2,
                generation_status="generating",
                active_generation_message_id=assistant_message_id,
                updated_at=now,
            )
            .returning(Conversation.next_sequence_number)
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row is None:
            return None

        returned_seq = row[0]
        user_seq = returned_seq - 2
        assistant_seq = returned_seq - 1
        return user_seq, assistant_seq

    async def release_generation_lock(
        self,
        conversation_id: UUID,
        assistant_message_id: UUID,
        set_last_message_at: bool = True,
    ) -> bool:
        """
        Fenced release of conversation generation lock.
        Only succeeds if active_generation_message_id still matches assistant_message_id.
        """
        now = datetime.now(timezone.utc)
        values: dict[str, Any] = {
            "generation_status": "idle",
            "active_generation_message_id": None,
            "updated_at": now,
        }
        if set_last_message_at:
            values["last_message_at"] = now

        stmt = (
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.active_generation_message_id == assistant_message_id,
            )
            .values(**values)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def reconcile_stale_generation(
        self,
        conversation_id: UUID,
        stale_threshold_seconds: int = 1200,
    ) -> bool:
        """
        Reconcile a conversation abandoned due to server crash or hard disconnect.
        Targets the active assistant message if created_at exceeds stale threshold.
        """
        # Step 1: Lock the conversation row
        lock_query = (
            select(Conversation.id, Conversation.active_generation_message_id)
            .where(
                Conversation.id == conversation_id,
                Conversation.generation_status == "generating",
                Conversation.deleted_at.is_(None),
            )
            .with_for_update()
        )
        lock_res = await self.session.execute(lock_query)
        conv_row = lock_res.fetchone()
        if conv_row is None or conv_row[1] is None:
            return False

        active_msg_id = conv_row[1]
        now = datetime.now(timezone.utc)
        threshold_dt = datetime.fromtimestamp(now.timestamp() - stale_threshold_seconds, tz=timezone.utc)

        # Step 2: Mark the stale active assistant message as interrupted
        msg_stmt = (
            update(Message)
            .where(
                Message.id == active_msg_id,
                Message.status.in_(["pending", "streaming"]),
                Message.created_at < threshold_dt,
            )
            .values(
                status="interrupted",
                completed_at=now,
                metadata_=Message.metadata_.concat(
                    func.jsonb_build_object("interrupted_reason", "stale_generation_timeout")
                ),
            )
        )
        msg_res = await self.session.execute(msg_stmt)
        if msg_res.rowcount == 0:
            return False

        # Step 3: Unlock the conversation row
        conv_stmt = (
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.active_generation_message_id == active_msg_id,
            )
            .values(
                generation_status="idle",
                active_generation_message_id=None,
                updated_at=now,
            )
        )
        await self.session.execute(conv_stmt)
        return True
