"""
Pure domain entities representing the core chat concepts.

These dataclasses are decoupled from SQLAlchemy ORM, database drivers, and frameworks.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from enterprise_ai_platform.domain.chat.enums import (
    ConversationStatus,
    GenerationStatus,
    MessageRole,
    MessageStatus,
    TitleSource,
)


@dataclass(slots=True)
class ConversationEntity:
    """Core domain representation of a dialogue session."""

    id: UUID
    user_id: UUID
    title: str
    title_source: TitleSource
    status: ConversationStatus
    is_pinned: bool
    last_message_at: datetime | None
    next_sequence_number: int
    generation_status: GenerationStatus
    active_generation_message_id: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(slots=True)
class MessageEntity:
    """Core domain representation of an individual message."""

    id: UUID
    conversation_id: UUID
    sequence_number: int
    role: MessageRole
    content: str
    status: MessageStatus
    client_message_id: UUID | None
    parent_message_id: UUID | None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(slots=True)
class MessageFeedbackEntity:
    """Core domain representation of feedback on an assistant message."""

    id: UUID
    message_id: UUID
    conversation_id: UUID
    user_id: UUID
    rating: int
    comment: str | None
    created_at: datetime


@dataclass(slots=True)
class ConversationSummaryEntity:
    """Core domain representation of a compressed conversation summary."""

    id: UUID
    conversation_id: UUID
    summary: str
    version: int
    summarized_through_sequence: int
    created_at: datetime
    updated_at: datetime
