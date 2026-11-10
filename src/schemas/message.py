"""
Pydantic v2 schemas for Message endpoints.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageSubmitRequest(BaseModel):
    """Payload for submitting a user message to initiate a chat turn."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=32768, description="User prompt text")
    client_message_id: UUID | None = Field(
        default=None,
        description="Client-generated UUID for idempotent submission",
    )


class MessageResponse(BaseModel):
    """Serialized representation of a message turn."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sequence_number: int
    role: str
    content: str
    status: str
    client_message_id: UUID | None
    parent_message_id: UUID | None
    metadata: dict[str, Any] = Field(default_factory=dict, alias="metadata_")
    created_at: datetime
    completed_at: datetime | None


class MessageHistoryResponse(BaseModel):
    """Paginated collection of conversation messages."""

    messages: list[MessageResponse]
    next_cursor: int | None = None
    has_more: bool = False
