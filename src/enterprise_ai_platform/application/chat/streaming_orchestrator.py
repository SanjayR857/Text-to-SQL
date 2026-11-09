"""
Streaming orchestrator implementation.

Coordinates real-time assistant token generation and Server-Sent Events (SSE) streaming.
Strictly adheres to the core architectural guarantee:
ZERO database connections are held during external LLM token generation.
"""
import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
import logging
from uuid import UUID, uuid4

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from enterprise_ai_platform.domain.conversations.exceptions import (
    ConversationNotFoundError,
    DuplicateMessageError,
    GenerationConflictError,
)
from enterprise_ai_platform.domain.conversations.protocols import (
    AIGeneratorProtocol,
    ContextMessage,
    GenerationContext,
    StreamChunk,
    SummaryGeneratorProtocol,
    TitleGeneratorProtocol,
)
from enterprise_ai_platform.infrastructure.database.repositories.conversation_repo import (
    ConversationRepository,
)
from enterprise_ai_platform.infrastructure.database.repositories.message_repo import (
    MessageRepository,
)
from enterprise_ai_platform.infrastructure.database.repositories.summary_repo import (
    SummaryRepository,
)
from enterprise_ai_platform.infrastructure.streaming.sse_formatter import (
    SSEFormatter,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TurnContext:
    """Pre-allocated context for an active conversation turn."""

    conversation_id: UUID
    user_id: UUID
    user_message_id: UUID
    user_sequence: int
    assistant_message_id: UUID
    assistant_sequence: int
    context: GenerationContext
    is_first_turn: bool


class StreamingOrchestrator:
    """
    Coordinates turn sequence reservation, external AI token generation,
    fenced persistence, and background titling/summarization tasks.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        ai_generator: AIGeneratorProtocol,
        title_generator: TitleGeneratorProtocol | None = None,
        summary_generator: SummaryGeneratorProtocol | None = None,
        sse_formatter: SSEFormatter | None = None,
        timeout_seconds: float = 900.0,
        keepalive_interval_seconds: float = 15.0,
        summary_threshold_sequence: int = 10,
        summary_step_interval: int = 10,
    ) -> None:
        self.session_factory = session_factory
        self.ai_generator = ai_generator
        self.title_generator = title_generator
        self.summary_generator = summary_generator
        self.sse_formatter = sse_formatter or SSEFormatter()
        self.timeout_seconds = timeout_seconds
        self.keepalive_interval_seconds = keepalive_interval_seconds
        self.summary_threshold_sequence = summary_threshold_sequence
        self.summary_step_interval = summary_step_interval

    async def prepare_turn(
        self,
        conversation_id: UUID,
        user_id: UUID,
        prompt: str,
        client_message_id: UUID | None = None,
    ) -> TurnContext:
        """
        Execute Transaction 1 (< 15ms):
        1. Validate conversation ownership and active state.
        2. Verify idempotency if client_message_id is supplied.
        3. Atomically reserve next sequence pair and acquire generation lock.
        4. Insert user message and pending assistant placeholder message.
        5. Assemble prior dialogue context.
        6. Commit and release database connection back to pool.
        """
        assistant_message_id = uuid4()

        async with self.session_factory() as session:
            async with session.begin():
                conv_repo = ConversationRepository(session)
                msg_repo = MessageRepository(session)
                summary_repo = SummaryRepository(session)

                # Step 1: Validate conversation
                conversation = await conv_repo.get_by_id(conversation_id, user_id)
                if conversation is None:
                    raise ConversationNotFoundError(conversation_id)

                # Step 2: Idempotency check on user messages
                if client_message_id is not None:
                    existing = await msg_repo.get_by_client_message_id(
                        conversation_id=conversation_id,
                        client_message_id=client_message_id,
                    )
                    if existing is not None:
                        raise DuplicateMessageError(
                            client_message_id=client_message_id,
                            existing_message_id=existing.id,
                        )

                # Step 3: Atomic reservation & lock
                seq_pair = await conv_repo.atomic_reserve_turn(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    assistant_message_id=assistant_message_id,
                )
                if seq_pair is None:
                    conv_check = await conv_repo.get_by_id(conversation_id, user_id)
                    if conv_check and conv_check.generation_status == "generating":
                        raise GenerationConflictError(conversation_id)
                    raise ConversationNotFoundError(conversation_id)

                user_seq, assistant_seq = seq_pair

                # Step 4: Persist user prompt and pending assistant placeholder
                user_msg, _ = await msg_repo.create_user_and_assistant_messages(
                    conversation_id=conversation_id,
                    user_sequence=user_seq,
                    user_content=prompt,
                    assistant_message_id=assistant_message_id,
                    assistant_sequence=assistant_seq,
                    client_message_id=client_message_id,
                )

                # Step 5: Assemble prior dialogue context (strictly < user_seq)
                prior_messages = await msg_repo.get_prior_context_messages(
                    conversation_id=conversation_id,
                    max_sequence=user_seq - 1,
                    limit=50,
                )
                context_messages = [
                    ContextMessage(
                        role=m.role,
                        content=m.content,
                        sequence_number=m.sequence_number,
                    )
                    for m in prior_messages
                ]

                latest_summary = await summary_repo.get_latest(conversation_id)
                summary_text = latest_summary.summary if latest_summary else None

                gen_context = GenerationContext(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    latest_summary=summary_text,
                    messages=context_messages,
                )

                is_first_turn = (user_seq == 1) or (conversation.title_source == "default")

        # Transaction 1 committed and DB connection closed upon block exit
        return TurnContext(
            conversation_id=conversation_id,
            user_id=user_id,
            user_message_id=user_msg.id,
            user_sequence=user_seq,
            assistant_message_id=assistant_message_id,
            assistant_sequence=assistant_seq,
            context=gen_context,
            is_first_turn=is_first_turn,
        )

    async def stream_response(
        self,
        turn_context: TurnContext,
        prompt: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream assistant tokens over SSE.
        ZERO DB connections are active during this execution.
        """
        # 1. Emit message_start immediately
        yield self.sse_formatter.format_message_start(
            message_id=turn_context.assistant_message_id,
            conversation_id=turn_context.conversation_id,
            sequence_number=turn_context.assistant_sequence,
        )

        accumulated_text: list[str] = []
        finish_reason = "stop"
        prompt_tokens: int | None = None
        completion_tokens: int | None = None
        chunk_index = 0
        generator = None

        try:
            # Wrap entire external generation in the 15-minute global timeout
            async with asyncio.timeout(self.timeout_seconds):
                generator = self.ai_generator.generate_stream(turn_context.context, prompt)
                stream_iter = generator.__aiter__()

                while True:
                    try:
                        # Wait for next token chunk with keepalive interval
                        chunk: StreamChunk = await asyncio.wait_for(
                            stream_iter.__anext__(),
                            timeout=self.keepalive_interval_seconds,
                        )
                    except TimeoutError:
                        # Emit keepalive heartbeat comment to prevent proxy idle disconnects
                        yield self.sse_formatter.format_keepalive()
                        continue
                    except StopAsyncIteration:
                        break

                    if chunk.delta:
                        accumulated_text.append(chunk.delta)
                        yield self.sse_formatter.format_content_delta(
                            delta=chunk.delta,
                            index=chunk_index,
                        )
                        chunk_index += 1

                    if chunk.is_finish:
                        if chunk.finish_reason:
                            finish_reason = chunk.finish_reason
                        if chunk.prompt_tokens is not None:
                            prompt_tokens = chunk.prompt_tokens
                        if chunk.completion_tokens is not None:
                            completion_tokens = chunk.completion_tokens
                        break

            full_content = "".join(accumulated_text)

            # Transaction 2: Persist completed message and release lock (< 15ms)
            await self._finalize_completed(
                turn_context=turn_context,
                full_content=full_content,
                finish_reason=finish_reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            # Terminal event
            yield self.sse_formatter.format_message_complete(
                message_id=turn_context.assistant_message_id,
                conversation_id=turn_context.conversation_id,
                finish_reason=finish_reason,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            # Asynchronous background tasks (titling & summarization)
            self._enqueue_background_tasks(
                turn_context=turn_context,
                prompt=prompt,
                full_response=full_content,
                background_tasks=background_tasks,
            )

        except (asyncio.CancelledError, GeneratorExit):
            # Client disconnected or request was cancelled
            full_content = "".join(accumulated_text)
            logger.info(
                "Client disconnected during generation for message %s. Saving partial content.",
                turn_context.assistant_message_id,
            )
            await self._finalize_interrupted(
                turn_context=turn_context,
                partial_content=full_content,
                reason="client_disconnect",
            )
            raise

        except TimeoutError:
            # 15-minute global timeout exceeded
            full_content = "".join(accumulated_text)
            logger.warning(
                "Generation timed out after %s seconds for message %s.",
                self.timeout_seconds,
                turn_context.assistant_message_id,
            )
            await self._finalize_interrupted(
                turn_context=turn_context,
                partial_content=full_content,
                reason="generation_timeout",
            )
            yield self.sse_formatter.format_error(
                code="GENERATION_TIMEOUT",
                message=f"Assistant response generation timed out after {int(self.timeout_seconds)} seconds.",
            )

        except Exception as exc:
            # External generator error or unexpected failure
            logger.exception(
                "Unexpected failure during generation for message %s: %s",
                turn_context.assistant_message_id,
                exc,
            )
            await self._finalize_failed(
                turn_context=turn_context,
                error_detail=str(exc),
            )
            yield self.sse_formatter.format_error(
                code="GENERATION_ERROR",
                message="An unexpected error occurred while generating the assistant response.",
            )

        finally:
            if generator is not None and hasattr(generator, "aclose"):
                try:
                    await generator.aclose()
                except Exception:
                    pass

    async def stream_turn(
        self,
        conversation_id: UUID,
        user_id: UUID,
        prompt: str,
        client_message_id: UUID | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> AsyncIterator[str]:
        """
        Unified end-to-end streaming turn entry point.
        Prepares turn sequence (Tx 1) and yields SSE event stream.
        """
        turn_ctx = await self.prepare_turn(
            conversation_id=conversation_id,
            user_id=user_id,
            prompt=prompt,
            client_message_id=client_message_id,
        )
        async for chunk in self.stream_response(
            turn_context=turn_ctx,
            prompt=prompt,
            background_tasks=background_tasks,
        ):
            yield chunk

    async def _finalize_completed(
        self,
        turn_context: TurnContext,
        full_content: str,
        finish_reason: str,
        prompt_tokens: int | None,
        completion_tokens: int | None,
    ) -> None:
        """Transaction 2: Fenced persistence of completed response (< 15ms)."""
        metadata = {
            "finish_reason": finish_reason,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        async with self.session_factory() as session:
            async with session.begin():
                msg_repo = MessageRepository(session)
                conv_repo = ConversationRepository(session)

                updated = await msg_repo.fenced_complete_message(
                    assistant_message_id=turn_context.assistant_message_id,
                    conversation_id=turn_context.conversation_id,
                    content=full_content,
                    metadata=metadata,
                )
                if updated:
                    await conv_repo.release_generation_lock(
                        conversation_id=turn_context.conversation_id,
                        assistant_message_id=turn_context.assistant_message_id,
                        set_last_message_at=True,
                    )
                else:
                    logger.warning(
                        "Fenced completion skipped for message %s: already superseded or reconciled.",
                        turn_context.assistant_message_id,
                    )

    async def _finalize_interrupted(
        self,
        turn_context: TurnContext,
        partial_content: str,
        reason: str,
    ) -> None:
        """Transaction 2: Fenced persistence of interrupted response (< 15ms)."""
        async with self.session_factory() as session:
            async with session.begin():
                msg_repo = MessageRepository(session)
                conv_repo = ConversationRepository(session)

                updated = await msg_repo.fenced_interrupt_message(
                    assistant_message_id=turn_context.assistant_message_id,
                    conversation_id=turn_context.conversation_id,
                    partial_content=partial_content,
                    reason=reason,
                )
                if updated:
                    await conv_repo.release_generation_lock(
                        conversation_id=turn_context.conversation_id,
                        assistant_message_id=turn_context.assistant_message_id,
                        set_last_message_at=True,
                    )
                else:
                    logger.warning(
                        "Fenced interrupt skipped for message %s: already superseded or reconciled.",
                        turn_context.assistant_message_id,
                    )

    async def _finalize_failed(
        self,
        turn_context: TurnContext,
        error_detail: str,
    ) -> None:
        """Transaction 2: Fenced persistence of failed response (< 15ms)."""
        async with self.session_factory() as session:
            async with session.begin():
                msg_repo = MessageRepository(session)
                conv_repo = ConversationRepository(session)

                updated = await msg_repo.fenced_fail_message(
                    assistant_message_id=turn_context.assistant_message_id,
                    conversation_id=turn_context.conversation_id,
                    error_detail=error_detail,
                )
                if updated:
                    await conv_repo.release_generation_lock(
                        conversation_id=turn_context.conversation_id,
                        assistant_message_id=turn_context.assistant_message_id,
                        set_last_message_at=False,
                    )
                else:
                    logger.warning(
                        "Fenced fail skipped for message %s: already superseded or reconciled.",
                        turn_context.assistant_message_id,
                    )

    def _enqueue_background_tasks(
        self,
        turn_context: TurnContext,
        prompt: str,
        full_response: str,
        background_tasks: BackgroundTasks | None,
    ) -> None:
        """Dispatch asynchronous conversation titling and rolling summarization."""
        # 1. Conversation Titling
        if turn_context.is_first_turn and self.title_generator is not None:
            if background_tasks is not None:
                background_tasks.add_task(
                    self._run_titling,
                    turn_context.conversation_id,
                    turn_context.user_id,
                    prompt,
                    full_response,
                )
            else:
                asyncio.create_task(
                    self._run_titling(
                        turn_context.conversation_id,
                        turn_context.user_id,
                        prompt,
                        full_response,
                    )
                )

        # 2. Rolling Summarization
        if (
            self.summary_generator is not None
            and turn_context.assistant_sequence >= self.summary_threshold_sequence
            and (turn_context.assistant_sequence % self.summary_step_interval == 0)
        ):
            if background_tasks is not None:
                background_tasks.add_task(
                    self._run_summarization,
                    turn_context.conversation_id,
                    turn_context.user_id,
                    turn_context.assistant_sequence,
                )
            else:
                asyncio.create_task(
                    self._run_summarization(
                        turn_context.conversation_id,
                        turn_context.user_id,
                        turn_context.assistant_sequence,
                    )
                )

    async def _run_titling(
        self,
        conversation_id: UUID,
        user_id: UUID,
        prompt: str,
        assistant_response: str,
    ) -> None:
        """Background titling worker."""
        if self.title_generator is None:
            return
        try:
            new_title = await self.title_generator.generate_title(prompt, assistant_response)
            if new_title and new_title.strip():
                async with self.session_factory() as session:
                    async with session.begin():
                        repo = ConversationRepository(session)
                        await repo.update_metadata(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            title=new_title.strip()[:255],
                            title_source="generated",
                        )
        except Exception as exc:
            logger.warning(
                "Background titling failed for conversation %s: %s",
                conversation_id,
                exc,
            )

    async def _run_summarization(
        self,
        conversation_id: UUID,
        user_id: UUID,
        target_sequence: int,
    ) -> None:
        """Background rolling summarization worker."""
        if self.summary_generator is None:
            return
        try:
            async with self.session_factory() as session:
                summary_repo = SummaryRepository(session)
                msg_repo = MessageRepository(session)

                latest = await summary_repo.get_latest(conversation_id)
                existing_summary = latest.summary if latest else None
                start_seq = (latest.summarized_through_sequence + 1) if latest else 1

                unsummarized = await msg_repo.get_history_cursor(
                    conversation_id=conversation_id,
                    cursor_sequence=start_seq - 1,
                    limit=100,
                )
                messages_to_summarize = [
                    ContextMessage(
                        role=m.role,
                        content=m.content,
                        sequence_number=m.sequence_number,
                    )
                    for m in unsummarized
                    if m.sequence_number <= target_sequence and m.status == "completed"
                ]

            if not messages_to_summarize:
                return

            new_summary_text = await self.summary_generator.generate_summary(
                existing_summary=existing_summary,
                new_messages=messages_to_summarize,
            )

            async with self.session_factory() as session:
                async with session.begin():
                    summary_repo = SummaryRepository(session)
                    await summary_repo.save_next_version(
                        conversation_id=conversation_id,
                        summary_text=new_summary_text,
                        summarized_through_sequence=target_sequence,
                    )
        except Exception as exc:
            logger.warning(
                "Background summarization failed for conversation %s: %s",
                conversation_id,
                exc,
            )
