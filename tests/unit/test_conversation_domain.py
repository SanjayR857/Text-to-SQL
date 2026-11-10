"""
Unit tests for domain layer entities, enums, exceptions, protocols, and SSE formatting.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from chat.conversation import (
    ConversationEntity,
    ConversationStatus,
    ConversationSummaryEntity,
    GenerationStatus,
    TitleSource,
)
from chat.exceptions import (
    ChatDomainException,
    ConversationNotFoundError,
    DuplicateMessageError,
    GenerationConflictError,
    GenerationFencingError,
    InvalidFeedbackError,
    MessageNotFoundError,
    StaleSummaryError,
)
from chat.message import (
    MessageEntity,
    MessageFeedbackEntity,
    MessageRole,
    MessageStatus,
)
from chat.protocols import (
    ContextMessage,
    GenerationContext,
    StreamChunk,
)
from chat.sse_formatter import (
    SSEFormatter,
)


def test_domain_enums():
    """Verify enumeration members and string values."""
    assert ConversationStatus.ACTIVE.value == "active"
    assert ConversationStatus.ARCHIVED.value == "archived"

    assert GenerationStatus.IDLE.value == "idle"
    assert GenerationStatus.GENERATING.value == "generating"

    assert TitleSource.DEFAULT.value == "default"
    assert TitleSource.GENERATED.value == "generated"
    assert TitleSource.USER.value == "user"

    assert MessageRole.USER.value == "user"
    assert MessageRole.ASSISTANT.value == "assistant"
    assert MessageRole.SYSTEM.value == "system"

    assert MessageStatus.PENDING.value == "pending"
    assert MessageStatus.STREAMING.value == "streaming"
    assert MessageStatus.COMPLETED.value == "completed"
    assert MessageStatus.FAILED.value == "failed"
    assert MessageStatus.INTERRUPTED.value == "interrupted"


def test_domain_entities():
    """Verify entity creation and field integrity."""
    conv_id = uuid4()
    user_id = uuid4()
    now = datetime.now(timezone.utc)

    conv = ConversationEntity(
        id=conv_id,
        user_id=user_id,
        title="Test Conversation",
        title_source=TitleSource.DEFAULT,
        status=ConversationStatus.ACTIVE,
        is_pinned=False,
        last_message_at=None,
        next_sequence_number=1,
        generation_status=GenerationStatus.IDLE,
        active_generation_message_id=None,
        created_at=now,
        updated_at=now,
    )
    assert conv.id == conv_id
    assert conv.title == "Test Conversation"
    assert conv.status == ConversationStatus.ACTIVE

    msg_id = uuid4()
    msg = MessageEntity(
        id=msg_id,
        conversation_id=conv_id,
        sequence_number=1,
        role=MessageRole.USER,
        content="Hello world",
        status=MessageStatus.COMPLETED,
        client_message_id=None,
        parent_message_id=None,
        created_at=now,
    )
    assert msg.sequence_number == 1
    assert msg.role == MessageRole.USER

    feedback = MessageFeedbackEntity(
        id=uuid4(),
        message_id=msg_id,
        conversation_id=conv_id,
        user_id=user_id,
        rating=1,
        comment="Great response",
        created_at=now,
    )
    assert feedback.rating == 1

    summary = ConversationSummaryEntity(
        id=uuid4(),
        conversation_id=conv_id,
        summary="Summary of dialogue",
        version=1,
        summarized_through_sequence=10,
        created_at=now,
        updated_at=now,
    )
    assert summary.version == 1
    assert summary.summarized_through_sequence == 10


def test_domain_exceptions():
    """Verify custom exception inheritance and attribute storage."""
    conv_id = uuid4()
    msg_id = uuid4()
    client_msg_id = uuid4()

    exc1 = ConversationNotFoundError(conv_id)
    assert isinstance(exc1, ChatDomainException)
    assert exc1.conversation_id == conv_id
    assert str(conv_id) in str(exc1)

    exc2 = MessageNotFoundError(msg_id)
    assert exc2.message_id == msg_id

    exc3 = GenerationConflictError(conv_id)
    assert "currently generating" in str(exc3)

    exc4 = GenerationFencingError(msg_id)
    assert exc4.assistant_message_id == msg_id

    exc5 = DuplicateMessageError(client_msg_id, msg_id)
    assert exc5.client_message_id == client_msg_id
    assert exc5.existing_message_id == msg_id

    exc6 = InvalidFeedbackError("Rating must be -1 or 1")
    assert "Rating must be -1 or 1" in str(exc6)

    exc7 = StaleSummaryError(sequence=5, latest_sequence=10)
    assert exc7.sequence == 5
    assert exc7.latest_sequence == 10


def test_domain_protocols_and_models():
    """Verify protocol models, immutability, and structures."""
    chunk = StreamChunk(
        delta="token",
        is_finish=True,
        finish_reason="stop",
        prompt_tokens=5,
        completion_tokens=10,
    )
    assert chunk.delta == "token"
    assert chunk.is_finish is True
    assert chunk.prompt_tokens == 5

    ctx_msg = ContextMessage(role="user", content="hello", sequence_number=1)
    assert ctx_msg.role == "user"

    gen_ctx = GenerationContext(
        conversation_id=uuid4(),
        user_id=uuid4(),
        latest_summary="Rolling summary",
        messages=[ctx_msg],
    )
    assert len(gen_ctx.messages) == 1
    assert gen_ctx.latest_summary == "Rolling summary"


def test_sse_formatter():
    """Verify SSEFormatter conforms to RFC specifications."""
    m_id = uuid4()
    c_id = uuid4()

    start = SSEFormatter.format_message_start(m_id, c_id, 2)
    assert start.startswith("event: message_start\ndata: ")
    assert str(m_id) in start
    assert start.endswith("\n\n")

    delta = SSEFormatter.format_content_delta("Hello", 0)
    assert delta == 'event: content_delta\ndata: {"delta":"Hello","index":0}\n\n'

    keepalive = SSEFormatter.format_keepalive()
    assert keepalive == ": keepalive\n\n"

    complete = SSEFormatter.format_message_complete(
        m_id, c_id, finish_reason="stop", prompt_tokens=10, completion_tokens=20
    )
    assert complete.startswith("event: message_complete\ndata: ")
    assert '"finish_reason":"stop"' in complete

    error = SSEFormatter.format_error("CODE_TEST", "Test error message")
    assert error == 'event: error\ndata: {"code":"CODE_TEST","message":"Test error message"}\n\n'
