"""
Domain exceptions for the Conversation Management Module.
"""
from uuid import UUID


class ConversationDomainException(Exception):
    """Base exception for all conversation domain violations."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# Backward-compatibility alias
ChatDomainException = ConversationDomainException


class ConversationNotFoundError(ConversationDomainException):
    """Raised when a requested conversation does not exist or user lacks ownership."""

    def __init__(self, conversation_id: UUID) -> None:
        super().__init__(f"Conversation {conversation_id} not found or access denied.")
        self.conversation_id = conversation_id


class MessageNotFoundError(ConversationDomainException):
    """Raised when a message cannot be located within a conversation."""

    def __init__(self, message_id: UUID) -> None:
        super().__init__(f"Message {message_id} not found.")
        self.message_id = message_id


class GenerationConflictError(ConversationDomainException):
    """Raised when a new message is submitted while a generation is actively running."""

    def __init__(self, conversation_id: UUID) -> None:
        super().__init__(
            f"Conversation {conversation_id} is currently generating. Concurrent messages are not permitted."
        )
        self.conversation_id = conversation_id


class GenerationFencingError(ConversationDomainException):
    """Raised when an active generation is fenced out due to cancellation, timeout, or supersede."""

    def __init__(self, assistant_message_id: UUID) -> None:
        super().__init__(
            f"Generation for message {assistant_message_id} was superseded or cancelled. Write aborted."
        )
        self.assistant_message_id = assistant_message_id


class DuplicateMessageError(ConversationDomainException):
    """Raised when an idempotent duplicate client_message_id is detected."""

    def __init__(self, client_message_id: UUID, existing_message_id: UUID) -> None:
        super().__init__(
            f"Duplicate message with client_message_id {client_message_id} already exists."
        )
        self.client_message_id = client_message_id
        self.existing_message_id = existing_message_id


class InvalidFeedbackError(ConversationDomainException):
    """Raised when feedback violates business rules (e.g. rating out of bounds or targeting user msg)."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid feedback submission: {reason}")


class StaleSummaryError(ConversationDomainException):
    """Raised when a summarization worker attempts an out-of-order sequence boundary update."""

    def __init__(self, sequence: int, latest_sequence: int) -> None:
        super().__init__(
            f"Cannot save summary for sequence {sequence}; current boundary is {latest_sequence}."
        )
        self.sequence = sequence
        self.latest_sequence = latest_sequence
