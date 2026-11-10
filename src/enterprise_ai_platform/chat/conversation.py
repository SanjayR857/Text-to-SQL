"""
Conversation domain entities and enums.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ConversationStatus(StrEnum):
    """Lifecycle status of a conversation."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class GenerationStatus(StrEnum):
    """In-flight generation lock state of a conversation."""

    IDLE = "idle"
    GENERATING = "generating"


class TitleSource(StrEnum):
    """Origin of the conversation title."""

    DEFAULT = "default"
    GENERATED = "generated"
    USER = "user"


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
class ConversationSummaryEntity:
    """Core domain representation of a compressed conversation summary."""

    id: UUID
    conversation_id: UUID
    summary: str
    version: int
    summarized_through_sequence: int
    created_at: datetime
    updated_at: datetime
