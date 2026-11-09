"""
Integration tests for Step 9: Streaming Orchestrator and Server-Sent Events (SSE).

Tests end-to-end SSE streaming, zero-connection holding, idempotency,
concurrency conflict, disconnect/interruption persistence, timeout handling,
and background titling against the live PostgreSQL database.
"""
import asyncio
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

from fastapi import FastAPI
import httpx
import pytest
from sqlalchemy import select

from enterprise_ai_platform.api.dependencies import (
    DEV_USER_ID,
    get_ai_generator,
    get_streaming_orchestrator,
    get_summary_generator,
    get_title_generator,
)
from enterprise_ai_platform.api.exception_handlers import register
from enterprise_ai_platform.api.routes.conversations import router as conv_router
from enterprise_ai_platform.api.routes.feedback import router as feedback_router
from enterprise_ai_platform.domain.chat.protocols import (
    GenerationContext,
    StreamChunk,
)
from enterprise_ai_platform.infrastructure.database.connection_manager import (
    close_engine,
)
from enterprise_ai_platform.infrastructure.database.models.chat import (
    Conversation,
    Message,
)
from enterprise_ai_platform.infrastructure.database.models.user import User
from enterprise_ai_platform.infrastructure.database.session import (
    async_db_session,
    get_session_factory,
    reset_session_factory,
)
from enterprise_ai_platform.infrastructure.streaming.mock_ai_generator import (
    MockAIGenerator,
    MockTitleGenerator,
)
from enterprise_ai_platform.infrastructure.streaming.sse_formatter import (
    SSEFormatter,
)


def create_test_app() -> FastAPI:
    """Create test FastAPI application with registered routes and handlers."""
    app = FastAPI(title="Streaming Test App")
    register(app)
    app.include_router(conv_router)
    app.include_router(feedback_router)
    return app


def parse_sse_events(sse_text: str) -> list[dict[str, str]]:
    """Parse raw SSE stream text into structured event dictionaries."""
    events = []
    current_event = {}
    lines = sse_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            if current_event:
                events.append(current_event)
                current_event = {}
            continue

        if line.startswith(":"):
            # SSE comment (e.g. keepalive)
            events.append({"comment": line[1:].strip()})
        elif ":" in line:
            field, val = line.split(":", 1)
            current_event[field.strip()] = val.strip()

    if current_event:
        events.append(current_event)

    return events


@pytest.mark.asyncio
async def test_sse_formatter_wire_syntax():
    """Verify standard RFC-compliant SSE wire formatting."""
    msg_id = uuid4()
    conv_id = uuid4()

    start_event = SSEFormatter.format_message_start(msg_id, conv_id, sequence_number=2)
    assert start_event.startswith("event: message_start\ndata: ")
    assert str(msg_id) in start_event
    assert start_event.endswith("\n\n")

    delta_event = SSEFormatter.format_content_delta("Hello", index=0)
    assert delta_event == 'event: content_delta\ndata: {"delta":"Hello","index":0}\n\n'

    keepalive = SSEFormatter.format_keepalive()
    assert keepalive == ": keepalive\n\n"

    complete_event = SSEFormatter.format_message_complete(
        msg_id, conv_id, finish_reason="stop", prompt_tokens=10, completion_tokens=20
    )
    assert complete_event.startswith("event: message_complete\ndata: ")
    assert '"finish_reason":"stop"' in complete_event

    error_event = SSEFormatter.format_error("TIMEOUT", "Generation timed out")
    assert error_event == 'event: error\ndata: {"code":"TIMEOUT","message":"Generation timed out"}\n\n'


@pytest.mark.asyncio
async def test_streaming_turn_e2e():
    """Verify full end-to-end turn generation over SSE."""
    app = create_test_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # Step 1: Create a conversation
        create_res = await client.post("/conversations", json={"title": "Test Streaming"})
        assert create_res.status_code == 201
        conv_id = create_res.json()["id"]

        # Step 2: Submit a message turn and consume SSE stream
        payload = {"content": "What is Text-to-SQL?"}
        stream_res = await client.post(
            f"/conversations/{conv_id}/messages",
            json=payload,
            headers={"X-User-ID": str(DEV_USER_ID)},
        )
        assert stream_res.status_code == 200
        assert "text/event-stream" in stream_res.headers["content-type"]

        body_text = stream_res.text
        events = parse_sse_events(body_text)

        # Step 3: Validate event sequence
        assert len(events) >= 3
        # First event is message_start
        assert events[0].get("event") == "message_start"
        assert "message_id" in events[0]["data"]
        assert "sequence_number" in events[0]["data"]

        # Intermediary content_delta events
        deltas = [e for e in events if e.get("event") == "content_delta"]
        assert len(deltas) > 0

        # Terminal event is message_complete
        complete_event = events[-1]
        assert complete_event.get("event") == "message_complete"
        assert '"finish_reason":"stop"' in complete_event["data"]

        # Step 4: Verify database persistence
        async with async_db_session() as session:
            # Verify user message (sequence 1)
            q_user = select(Message).where(
                Message.conversation_id == UUID(conv_id),
                Message.sequence_number == 1,
            )
            user_msg = (await session.execute(q_user)).scalar_one()
            assert user_msg.role == "user"
            assert user_msg.content == "What is Text-to-SQL?"
            assert user_msg.status == "completed"

            # Verify assistant message (sequence 2)
            q_asst = select(Message).where(
                Message.conversation_id == UUID(conv_id),
                Message.sequence_number == 2,
            )
            asst_msg = (await session.execute(q_asst)).scalar_one()
            assert asst_msg.role == "assistant"
            assert asst_msg.status == "completed"
            assert "What is Text-to-SQL?" in asst_msg.content
            assert asst_msg.completed_at is not None

            # Verify conversation generation lock is released
            q_conv = select(Conversation).where(Conversation.id == UUID(conv_id))
            conv = (await session.execute(q_conv)).scalar_one()
            assert conv.generation_status == "idle"
            assert conv.active_generation_message_id is None
            assert conv.last_message_at is not None
            assert conv.next_sequence_number == 3


@pytest.mark.asyncio
async def test_idempotency_duplicate_client_message_id():
    """Verify that duplicate client_message_id returns 409 Conflict immediately."""
    app = create_test_app()
    client_msg_id = uuid4()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # Create conversation
        create_res = await client.post("/conversations", json={"title": "Idempotency Test"})
        conv_id = create_res.json()["id"]

        # First submission with client_message_id
        res1 = await client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": "First call", "client_message_id": str(client_msg_id)},
            headers={"X-User-ID": str(DEV_USER_ID)},
        )
        assert res1.status_code == 200

        # Duplicate submission with same client_message_id
        res2 = await client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": "Duplicate call", "client_message_id": str(client_msg_id)},
            headers={"X-User-ID": str(DEV_USER_ID)},
        )
        assert res2.status_code == 409
        assert "Duplicate message submission detected" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_concurrent_generation_conflict():
    """Verify submitting a message while conversation is generating returns 409 Conflict."""
    app = create_test_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        create_res = await client.post("/conversations", json={"title": "Lock Conflict Test"})
        conv_id = create_res.json()["id"]

        # Manually acquire generation lock in DB
        dummy_msg_id = uuid4()
        async with async_db_session() as session:
            conv = (
                await session.execute(
                    select(Conversation).where(Conversation.id == UUID(conv_id))
                )
            ).scalar_one()
            # Insert a dummy placeholder message first to satisfy composite FK
            msg = Message(
                id=dummy_msg_id,
                conversation_id=UUID(conv_id),
                sequence_number=99,
                role="assistant",
                content="",
                status="pending",
                metadata_={},
            )
            session.add(msg)
            await session.flush()

            conv.generation_status = "generating"
            conv.active_generation_message_id = dummy_msg_id
            await session.flush()

        # Submit message turn while generating
        conflict_res = await client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": "This should fail with 409 conflict"},
            headers={"X-User-ID": str(DEV_USER_ID)},
        )
        assert conflict_res.status_code == 409
        assert "Generation currently in progress" in conflict_res.json()["detail"]


@pytest.mark.asyncio
async def test_generator_failure_handling():
    """Verify that external generator exceptions persist message as failed and emit error event."""
    app = create_test_app()

    class FailingAIGenerator:
        async def generate_stream(self, context, prompt):
            yield StreamChunk(delta="Starting...")
            raise RuntimeError("LLM downstream service unavailable")

    app.dependency_overrides[get_ai_generator] = lambda: FailingAIGenerator()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        create_res = await client.post("/conversations", json={"title": "Failure Test"})
        conv_id = create_res.json()["id"]

        res = await client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": "Trigger failure"},
            headers={"X-User-ID": str(DEV_USER_ID)},
        )
        assert res.status_code == 200
        events = parse_sse_events(res.text)

        # Verify error event was emitted
        error_events = [e for e in events if e.get("event") == "error"]
        assert len(error_events) == 1
        assert "GENERATION_ERROR" in error_events[0]["data"]

        # Verify DB state: message is marked failed and lock released
        async with async_db_session() as session:
            q_asst = select(Message).where(
                Message.conversation_id == UUID(conv_id),
                Message.role == "assistant",
            )
            asst_msg = (await session.execute(q_asst)).scalar_one()
            assert asst_msg.status == "failed"
            assert "LLM downstream service unavailable" in str(asst_msg.metadata_)

            q_conv = select(Conversation).where(Conversation.id == UUID(conv_id))
            conv = (await session.execute(q_conv)).scalar_one()
            assert conv.generation_status == "idle"
            assert conv.active_generation_message_id is None


@pytest.mark.asyncio
async def test_client_disconnect_saves_partial_content():
    """Verify that client cancellation preserves partial tokens and releases lock."""
    from enterprise_ai_platform.application.chat.streaming_orchestrator import (
        StreamingOrchestrator,
    )

    class AbortAIGenerator:
        async def generate_stream(self, context, prompt):
            yield StreamChunk(delta="Partial text before disconnect")
            raise asyncio.CancelledError()

    orchestrator = StreamingOrchestrator(
        session_factory=get_session_factory(),
        ai_generator=AbortAIGenerator(),
    )

    # Create conversation
    async with async_db_session() as session:
        from enterprise_ai_platform.infrastructure.database.repositories.conversation_repo import (
            ConversationRepository,
        )
        conv_repo = ConversationRepository(session)
        conv = await conv_repo.create(user_id=DEV_USER_ID, title="Disconnect Test")
        conv_id = conv.id

    turn_ctx = await orchestrator.prepare_turn(
        conversation_id=conv_id,
        user_id=DEV_USER_ID,
        prompt="Simulate disconnect",
    )

    # Consume stream and catch CancelledError
    with pytest.raises(asyncio.CancelledError):
        async for chunk in orchestrator.stream_response(turn_ctx, prompt="Simulate disconnect"):
            pass

    # Verify DB state: assistant message marked interrupted with partial content
    async with async_db_session() as session:
        q_asst = select(Message).where(
            Message.conversation_id == conv_id,
            Message.id == turn_ctx.assistant_message_id,
        )
        asst_msg = (await session.execute(q_asst)).scalar_one()
        assert asst_msg.status == "interrupted"
        assert asst_msg.content == "Partial text before disconnect"
        assert asst_msg.metadata_["interrupted_reason"] == "client_disconnect"

        q_conv = select(Conversation).where(Conversation.id == conv_id)
        conv = (await session.execute(q_conv)).scalar_one()
        assert conv.generation_status == "idle"
        assert conv.active_generation_message_id is None


@pytest.mark.asyncio
async def test_timeout_handling():
    """Verify that exceeding global timeout interrupts generation and emits timeout error event."""
    from enterprise_ai_platform.application.chat.streaming_orchestrator import (
        StreamingOrchestrator,
    )

    class HangingAIGenerator:
        async def generate_stream(self, context, prompt):
            yield StreamChunk(delta="First token")
            await asyncio.sleep(1.0)
            yield StreamChunk(delta="Never reached")

    orchestrator = StreamingOrchestrator(
        session_factory=get_session_factory(),
        ai_generator=HangingAIGenerator(),
        timeout_seconds=0.05,  # Force rapid timeout
    )

    async with async_db_session() as session:
        from enterprise_ai_platform.infrastructure.database.repositories.conversation_repo import (
            ConversationRepository,
        )
        conv_repo = ConversationRepository(session)
        conv = await conv_repo.create(user_id=DEV_USER_ID, title="Timeout Test")
        conv_id = conv.id

    turn_ctx = await orchestrator.prepare_turn(
        conversation_id=conv_id,
        user_id=DEV_USER_ID,
        prompt="Hanging query",
    )

    chunks = []
    async for chunk in orchestrator.stream_response(turn_ctx, prompt="Hanging query"):
        chunks.append(chunk)

    all_text = "".join(chunks)
    events = parse_sse_events(all_text)

    # Verify timeout error event was emitted
    error_events = [e for e in events if e.get("event") == "error"]
    assert len(error_events) == 1
    assert "GENERATION_TIMEOUT" in error_events[0]["data"]

    # Verify DB state: assistant message marked interrupted with generation_timeout
    async with async_db_session() as session:
        q_asst = select(Message).where(
            Message.conversation_id == conv_id,
            Message.id == turn_ctx.assistant_message_id,
        )
        asst_msg = (await session.execute(q_asst)).scalar_one()
        assert asst_msg.status == "interrupted"
        assert asst_msg.content == "First token"
        assert asst_msg.metadata_["interrupted_reason"] == "generation_timeout"

        q_conv = select(Conversation).where(Conversation.id == conv_id)
        conv = (await session.execute(q_conv)).scalar_one()
        assert conv.generation_status == "idle"
        assert conv.active_generation_message_id is None


@pytest.mark.asyncio
async def test_keepalive_emitted_during_delay():
    """Verify that keepalive comment lines are emitted when token generation has latency."""
    from enterprise_ai_platform.application.chat.streaming_orchestrator import (
        StreamingOrchestrator,
    )

    class SlowAIGenerator:
        async def generate_stream(self, context, prompt):
            yield StreamChunk(delta="Chunk 1")
            await asyncio.sleep(0.08)  # Exceed keepalive interval
            yield StreamChunk(delta="Chunk 2")
            yield StreamChunk(delta="", is_finish=True)

    orchestrator = StreamingOrchestrator(
        session_factory=get_session_factory(),
        ai_generator=SlowAIGenerator(),
        keepalive_interval_seconds=0.03,  # Emit keepalive quickly
    )

    async with async_db_session() as session:
        from enterprise_ai_platform.infrastructure.database.repositories.conversation_repo import (
            ConversationRepository,
        )
        conv_repo = ConversationRepository(session)
        conv = await conv_repo.create(user_id=DEV_USER_ID, title="Keepalive Test")
        conv_id = conv.id

    turn_ctx = await orchestrator.prepare_turn(
        conversation_id=conv_id,
        user_id=DEV_USER_ID,
        prompt="Slow query",
    )

    chunks = []
    async for chunk in orchestrator.stream_response(turn_ctx, prompt="Slow query"):
        chunks.append(chunk)

    all_text = "".join(chunks)
    assert ": keepalive\n\n" in all_text


@pytest.mark.asyncio
async def test_background_titling_execution():
    """Verify that background titling updates conversation title on first turn."""
    app = create_test_app()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        # Create conversation with default title
        create_res = await client.post("/conversations", json={})
        assert create_res.status_code == 201
        conv_id = create_res.json()["id"]
        assert create_res.json()["title_source"] == "default"

        # Submit message turn
        stream_res = await client.post(
            f"/conversations/{conv_id}/messages",
            json={"content": "Revenue analysis for Q3 2026"},
            headers={"X-User-ID": str(DEV_USER_ID)},
        )
        assert stream_res.status_code == 200

        # Allow FastAPI background task to finish
        await asyncio.sleep(0.1)

        # Verify conversation title was updated by background task
        async with async_db_session() as session:
            q_conv = select(Conversation).where(Conversation.id == UUID(conv_id))
            conv = (await session.execute(q_conv)).scalar_one()
            assert conv.title_source == "generated"
            assert "Revenue Analysis For Q3 2026" in conv.title


@pytest.mark.asyncio
async def test_background_summarization_execution():
    """Verify that background summarization creates a new version when threshold is met."""
    from enterprise_ai_platform.application.chat.streaming_orchestrator import (
        StreamingOrchestrator,
    )
    from enterprise_ai_platform.infrastructure.database.models.chat import (
        ConversationSummary,
    )
    from enterprise_ai_platform.infrastructure.streaming.mock_ai_generator import (
        MockSummaryGenerator,
    )

    orchestrator = StreamingOrchestrator(
        session_factory=get_session_factory(),
        ai_generator=MockAIGenerator(),
        summary_generator=MockSummaryGenerator(),
        summary_threshold_sequence=2,  # Trigger on turn 2
        summary_step_interval=2,
    )

    async with async_db_session() as session:
        from enterprise_ai_platform.infrastructure.database.repositories.conversation_repo import (
            ConversationRepository,
        )
        conv_repo = ConversationRepository(session)
        conv = await conv_repo.create(user_id=DEV_USER_ID, title="Summary Test")
        conv_id = conv.id

    # Execute turn 1 (assistant seq = 2)
    async for _ in orchestrator.stream_turn(
        conversation_id=conv_id,
        user_id=DEV_USER_ID,
        prompt="First dialogue turn",
    ):
        pass

    # Allow background task to complete
    await asyncio.sleep(0.1)

    # Verify summary version 1 was created
    async with async_db_session() as session:
        q_sum = (
            select(ConversationSummary)
            .where(ConversationSummary.conversation_id == conv_id)
            .order_by(ConversationSummary.version.desc())
        )
        summary = (await session.execute(q_sum)).scalar_one_or_none()
        assert summary is not None
        assert summary.version == 1
        assert summary.summarized_through_sequence == 2
        assert "Summary of the first" in summary.summary

