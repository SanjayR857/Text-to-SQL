"""
Message domain entities and enums.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class MessageRole(StrEnum):
    """Dialogue participant role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(StrEnum):
    """Granular delivery and lifecycle status of a message."""

    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


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
