"""
Pydantic v2 schemas for Conversation endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreateRequest(BaseModel):
    """Payload for creating a new conversation."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        max_length=255,
        description="Optional title for the conversation. Defaults to 'New Conversation'.",
    )


class ConversationUpdateRequest(BaseModel):
    """Payload for updating mutable conversation attributes."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=255)
    is_pinned: bool | None = Field(default=None)
    status: str | None = Field(
        default=None,
        pattern="^(active|archived)$",
        description="Allowed values: 'active', 'archived'",
    )


class ConversationResponse(BaseModel):
    """Serialized representation of a conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    title_source: str
    status: str
    is_pinned: bool
    last_message_at: datetime | None
    next_sequence_number: int
    generation_status: str
    active_generation_message_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """Paginated response containing conversations and pagination cursors."""

    items: list[ConversationResponse]
    next_cursor_last_message_at: datetime | None = None
    next_cursor_id: UUID | None = None
    has_more: bool = False
