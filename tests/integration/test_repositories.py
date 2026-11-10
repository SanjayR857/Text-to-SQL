"""
Integration tests for ConversationRepository, MessageRepository, SummaryRepository,
and FeedbackRepository against PostgreSQL.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from enterprise_ai_platform.api.dependencies import DEV_USER_ID
from enterprise_ai_platform.chat.models import (
    Conversation,
    Message,
)
from enterprise_ai_platform.chat.repositories.conversation_repo import (
    ConversationRepository,
)
from enterprise_ai_platform.chat.repositories.feedback_repo import (
    FeedbackRepository,
)
from enterprise_ai_platform.chat.repositories.message_repo import (
    MessageRepository,
)
from enterprise_ai_platform.chat.repositories.summary_repo import (
    SummaryRepository,
)
from enterprise_ai_platform.core.database import (
    async_db_session,
)
from tests.conftest import OTHER_USER_ID


@pytest.mark.asyncio
async def test_conversation_repo_lifecycle():
    """Verify conversation CRUD, ownership isolation, metadata updates, and soft deletion."""
    async with async_db_session() as session:
        repo = ConversationRepository(session)

        # 1. Create
        conv = await repo.create(user_id=DEV_USER_ID, title="Initial Title")
        conv_id = conv.id
        assert conv.title == "Initial Title"
        assert conv.generation_status == "idle"
        assert conv.next_sequence_number == 1
        assert conv.is_pinned is False

        # 2. Get by ID - Owner
        fetched = await repo.get_by_id(conv_id, DEV_USER_ID)
        assert fetched is not None
        assert fetched.id == conv_id

        # 3. Ownership isolation - Other user cannot fetch
        denied = await repo.get_by_id(conv_id, OTHER_USER_ID)
        assert denied is None

        # 4. Update metadata
        updated = await repo.update_metadata(
            conv_id, DEV_USER_ID, title="Updated Title", is_pinned=True
        )
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.is_pinned is True

        # 5. Soft delete
        deleted = await repo.soft_delete(conv_id, DEV_USER_ID)
        assert deleted is True

        # 6. Verify soft-deleted conversation is hidden
        hidden = await repo.get_by_id(conv_id, DEV_USER_ID)
        assert hidden is None


@pytest.mark.asyncio
async def test_conversation_repo_atomic_reservation_and_lock():
    """Verify atomic sequence number reservation and generation lock fencing."""
    async with async_db_session() as session:
        repo = ConversationRepository(session)
        conv = await repo.create(user_id=DEV_USER_ID, title="Lock Test")
        conv_id = conv.id

        asst_id_1 = uuid4()

        # 1. First reservation succeeds
        seq_pair = await repo.atomic_reserve_turn(conv_id, DEV_USER_ID, asst_id_1)
        assert seq_pair is not None
        user_seq, asst_seq = seq_pair
        assert user_seq == 1
        assert asst_seq == 2

        # 2. Concurrent reservation while generating is rejected
        asst_id_2 = uuid4()
        conflict_pair = await repo.atomic_reserve_turn(conv_id, DEV_USER_ID, asst_id_2)
        assert conflict_pair is None

        # 3. Release lock with wrong assistant ID fails
        wrong_id = uuid4()
        released = await repo.release_generation_lock(conv_id, wrong_id)
        assert released is False

        # 4. Release lock with valid assistant ID succeeds
        released_ok = await repo.release_generation_lock(conv_id, asst_id_1)
        assert released_ok is True

        # 5. Next reservation now succeeds with monotonic sequence progression
        seq_pair_2 = await repo.atomic_reserve_turn(conv_id, DEV_USER_ID, asst_id_2)
        assert seq_pair_2 is not None
        assert seq_pair_2 == (3, 4)

        # Cleanup lock
        await repo.release_generation_lock(conv_id, asst_id_2)


@pytest.mark.asyncio
async def test_conversation_repo_stale_reconciliation():
    """Verify stale generation reconciliation marks active message as interrupted."""
    async with async_db_session() as session:
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = await conv_repo.create(user_id=DEV_USER_ID, title="Stale Test")
        asst_id = uuid4()

        # Reserve turn
        seq_pair = await conv_repo.atomic_reserve_turn(conv.id, DEV_USER_ID, asst_id)
        assert seq_pair is not None

        # Create message pair
        await msg_repo.create_user_and_assistant_messages(
            conversation_id=conv.id,
            user_sequence=seq_pair[0],
            user_content="Prompt",
            assistant_message_id=asst_id,
            assistant_sequence=seq_pair[1],
        )

        # Manually backdate message created_at by 30 minutes
        thirty_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
        await session.execute(
            Message.__table__.update()
            .where(Message.id == asst_id)
            .values(created_at=thirty_mins_ago)
        )

        # Reconcile stale generation
        reconciled = await conv_repo.reconcile_stale_generation(conv.id, stale_threshold_seconds=600)
        assert reconciled is True

        # Verify message state
        asst_msg = await msg_repo.get_by_id(asst_id, conv.id)
        assert asst_msg is not None
        assert asst_msg.status == "interrupted"
        assert asst_msg.metadata_["interrupted_reason"] == "stale_generation_timeout"

        # Verify conversation state by refreshing ORM instance
        await session.refresh(conv)
        assert conv.generation_status == "idle"
        assert conv.active_generation_message_id is None


@pytest.mark.asyncio
async def test_message_repo_fenced_lifecycle():
    """Verify MessageRepository insertion, cursor history, prior context, and fenced states."""
    async with async_db_session() as session:
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)

        conv = await conv_repo.create(user_id=DEV_USER_ID, title="Message Lifecycle")
        asst_id = uuid4()
        client_msg_id = uuid4()

        # 1. Create turn pair
        user_msg, asst_msg = await msg_repo.create_user_and_assistant_messages(
            conversation_id=conv.id,
            user_sequence=1,
            user_content="What is SQL?",
            assistant_message_id=asst_id,
            assistant_sequence=2,
            client_message_id=client_msg_id,
        )
        assert user_msg.sequence_number == 1
        assert user_msg.client_message_id == client_msg_id
        assert asst_msg.sequence_number == 2
        assert asst_msg.parent_message_id == user_msg.id
        assert asst_msg.status == "pending"

        # 2. Idempotency lookup
        existing = await msg_repo.get_by_client_message_id(conv.id, client_msg_id)
        assert existing is not None
        assert existing.id == user_msg.id

        # 3. Prior context before sequence 1 is empty
        prior = await msg_repo.get_prior_context_messages(conv.id, max_sequence=0)
        assert len(prior) == 0

        # 4. Fenced completion
        completed_ok = await msg_repo.fenced_complete_message(
            assistant_message_id=asst_id,
            conversation_id=conv.id,
            content="SQL is Structured Query Language.",
            metadata={"model": "test-gpt"},
        )
        assert completed_ok is True

        # 5. Subsequent fenced complete fails (status is already completed, not pending/streaming)
        second_complete = await msg_repo.fenced_complete_message(
            assistant_message_id=asst_id,
            conversation_id=conv.id,
            content="Double write",
        )
        assert second_complete is False

        # 6. Prior context before sequence 3 now contains user and assistant
        prior_turn2 = await msg_repo.get_prior_context_messages(conv.id, max_sequence=2)
        assert len(prior_turn2) == 2
        assert prior_turn2[0].sequence_number == 1
        assert prior_turn2[1].sequence_number == 2


@pytest.mark.asyncio
async def test_summary_repo_monotonic_progression():
    """Verify SummaryRepository strictly enforces monotonic boundary progression and FOR UPDATE serialization."""
    async with async_db_session() as session:
        conv_repo = ConversationRepository(session)
        sum_repo = SummaryRepository(session)

        conv = await conv_repo.create(user_id=DEV_USER_ID, title="Summary Progression")

        # 1. Initially no summary
        latest = await sum_repo.get_latest(conv.id)
        assert latest is None

        # 2. Save version 1 (watermark sequence 4)
        v1 = await sum_repo.save_next_version(
            conversation_id=conv.id,
            summary_text="Summary up to turn 4",
            summarized_through_sequence=4,
        )
        assert v1 is not None
        assert v1.version == 1
        assert v1.summarized_through_sequence == 4

        # 3. Out-of-order summary worker finishing with sequence 2 is discarded (returns None)
        stale = await sum_repo.save_next_version(
            conversation_id=conv.id,
            summary_text="Stale summary for turn 2",
            summarized_through_sequence=2,
        )
        assert stale is None

        # 4. Same watermark boundary (4) is also discarded
        duplicate = await sum_repo.save_next_version(
            conversation_id=conv.id,
            summary_text="Duplicate boundary",
            summarized_through_sequence=4,
        )
        assert duplicate is None

        # 5. Save version 2 (watermark sequence 8) succeeds
        v2 = await sum_repo.save_next_version(
            conversation_id=conv.id,
            summary_text="Summary up to turn 8",
            summarized_through_sequence=8,
        )
        assert v2 is not None
        assert v2.version == 2
        assert v2.summarized_through_sequence == 8

        # 6. Verify get_latest returns version 2
        latest = await sum_repo.get_latest(conv.id)
        assert latest is not None
        assert latest.version == 2


@pytest.mark.asyncio
async def test_feedback_repo_upsert():
    """Verify FeedbackRepository composite upsert and unique message/user semantics."""
    async with async_db_session() as session:
        conv_repo = ConversationRepository(session)
        msg_repo = MessageRepository(session)
        feed_repo = FeedbackRepository(session)

        conv = await conv_repo.create(user_id=DEV_USER_ID, title="Feedback Test")
        asst_id = uuid4()
        _, asst_msg = await msg_repo.create_user_and_assistant_messages(
            conversation_id=conv.id,
            user_sequence=1,
            user_content="Prompt",
            assistant_message_id=asst_id,
            assistant_sequence=2,
        )

        # 1. Insert initial positive feedback (+1)
        fb1 = await feed_repo.upsert(
            message_id=asst_id,
            conversation_id=conv.id,
            user_id=DEV_USER_ID,
            rating=1,
            comment="Very helpful",
        )
        assert fb1.rating == 1
        assert fb1.comment == "Very helpful"

        # 2. Upsert to rating 4 with updated comment
        fb2 = await feed_repo.upsert(
            message_id=asst_id,
            conversation_id=conv.id,
            user_id=DEV_USER_ID,
            rating=4,
            comment="Actually had a minor inaccuracy",
        )
        assert fb2.id == fb1.id
        assert fb2.rating == 4
        assert fb2.comment == "Actually had a minor inaccuracy"

        # 3. Query feedback
        fetched = await feed_repo.get_by_message_and_user(asst_id, DEV_USER_ID)
        assert fetched is not None
        assert fetched.rating == 4
