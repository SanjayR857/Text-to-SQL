"""
Domain enumerations representing valid lifecycle states and categories.
"""
from enum import Enum


class ConversationStatus(str, Enum):
    """Lifecycle status of a conversation."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class GenerationStatus(str, Enum):
    """In-flight generation lock state of a conversation."""

    IDLE = "idle"
    GENERATING = "generating"


class TitleSource(str, Enum):
    """Origin of the conversation title."""

    DEFAULT = "default"
    GENERATED = "generated"
    USER = "user"


class MessageRole(str, Enum):
    """Dialogue participant role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Granular delivery and lifecycle status of a message."""

    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
