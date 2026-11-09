"""
Conversation API endpoints.

Exposes REST operations for conversation lifecycle management, metadata updates,
soft deletion, cursor-paginated message history retrieval, and real-time SSE streaming.
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import StreamingResponse

from enterprise_ai_platform.api.dependencies import (
    get_conversation_service,
    get_current_user_id,
    get_message_service,
    get_streaming_orchestrator,
)
from enterprise_ai_platform.api.schemas.conversation import (
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdateRequest,
)
from enterprise_ai_platform.api.schemas.message import (
    MessageHistoryResponse,
    MessageResponse,
    MessageSubmitRequest,
)
from enterprise_ai_platform.application.chat.conversation_service import (
    ConversationService,
)
from enterprise_ai_platform.application.chat.message_service import MessageService
from enterprise_ai_platform.application.chat.streaming_orchestrator import (
    StreamingOrchestrator,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
)
async def create_conversation(
    payload: ConversationCreateRequest | None = None,
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Create a new conversation session for the authenticated user."""
    title = payload.title if payload else None
    conversation = await service.create_conversation(user_id=user_id, title=title)
    return ConversationResponse.model_validate(conversation)


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List conversations",
)
async def list_conversations(
    cursor_last_message_at: datetime | None = Query(
        default=None,
        description="Cursor timestamp for pagination",
    ),
    cursor_id: UUID | None = Query(
        default=None,
        description="Tiebreaker cursor UUID for pagination",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    """List active conversations for the authenticated user, paginated via cursor."""
    items = await service.list_conversations(
        user_id=user_id,
        cursor_last_message_at=cursor_last_message_at,
        cursor_id=cursor_id,
        limit=limit + 1,
    )

    has_more = len(items) > limit
    paginated_items = items[:limit]

    next_cursor_last_message_at = None
    next_cursor_id = None
    if has_more and paginated_items:
        last_item = paginated_items[-1]
        next_cursor_last_message_at = last_item.last_message_at
        next_cursor_id = last_item.id

    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in paginated_items],
        next_cursor_last_message_at=next_cursor_last_message_at,
        next_cursor_id=next_cursor_id,
        has_more=has_more,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation details",
)
async def get_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Fetch metadata for a single conversation, verifying user ownership."""
    conversation = await service.get_conversation(conversation_id, user_id)
    return ConversationResponse.model_validate(conversation)


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update conversation metadata",
)
async def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Update title, pinned status, or archival status of a conversation."""
    updated = await service.update_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        title=payload.title,
        is_pinned=payload.is_pinned,
        status=payload.status,
    )
    return ConversationResponse.model_validate(updated)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete conversation",
)
async def delete_conversation(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ConversationService = Depends(get_conversation_service),
) -> None:
    """Soft-delete a conversation, hiding it and its messages from read endpoints."""
    await service.soft_delete_conversation(conversation_id, user_id)


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation message history",
)
async def get_conversation_history(
    conversation_id: UUID,
    cursor_sequence: int | None = Query(
        default=None,
        description="Pagination cursor: return messages with sequence_number > cursor_sequence",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    user_id: UUID = Depends(get_current_user_id),
    message_service: MessageService = Depends(get_message_service),
) -> MessageHistoryResponse:
    """Retrieve chronological message turns for a conversation using cursor pagination."""
    messages = await message_service.get_conversation_history(
        conversation_id=conversation_id,
        user_id=user_id,
        cursor_sequence=cursor_sequence,
        limit=limit + 1,
    )

    has_more = len(messages) > limit
    paginated_messages = messages[:limit]

    next_cursor = paginated_messages[-1].sequence_number if (has_more and paginated_messages) else None

    return MessageHistoryResponse(
        messages=[MessageResponse.model_validate(m) for m in paginated_messages],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.post(
    "/{conversation_id}/messages",
    summary="Submit message turn and stream assistant response",
    status_code=status.HTTP_200_OK,
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Server-Sent Events (SSE) stream of assistant token chunks",
            "content": {"text/event-stream": {}},
        },
        400: {"description": "Validation error or invalid request payload"},
        404: {"description": "Conversation not found or access denied"},
        409: {"description": "Concurrent generation already in progress or duplicate message"},
    },
)
async def submit_message(
    conversation_id: UUID,
    payload: MessageSubmitRequest,
    background_tasks: BackgroundTasks,
    user_id: UUID = Depends(get_current_user_id),
    orchestrator: StreamingOrchestrator = Depends(get_streaming_orchestrator),
) -> StreamingResponse:
    """
    Submit a user message turn and receive a real-time Server-Sent Events stream.

    Acquires the conversation generation lock and creates the assistant placeholder message
    in an initial short transaction (< 15ms). Streams incremental token deltas, heartbeats,
    and completion status with zero active database connections.
    """
    turn_ctx = await orchestrator.prepare_turn(
        conversation_id=conversation_id,
        user_id=user_id,
        prompt=payload.content,
        client_message_id=payload.client_message_id,
    )

    return StreamingResponse(
        orchestrator.stream_response(
            turn_context=turn_ctx,
            prompt=payload.content,
            background_tasks=background_tasks,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
