"""
Server-Sent Events (SSE) formatter.

Formats typed domain streaming events into RFC-compliant Server-Sent Events protocol messages.
"""
import json
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SSEMessageStartData(BaseModel):
    """Payload for message_start event."""

    model_config = ConfigDict(frozen=True)

    message_id: UUID
    conversation_id: UUID
    role: str = "assistant"
    sequence_number: int


class SSEContentDeltaData(BaseModel):
    """Payload for content_delta event."""

    model_config = ConfigDict(frozen=True)

    delta: str
    index: int


class SSEMessageCompleteData(BaseModel):
    """Payload for message_complete event."""

    model_config = ConfigDict(frozen=True)

    message_id: UUID
    conversation_id: UUID
    finish_reason: str = "stop"
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class SSEErrorData(BaseModel):
    """Payload for error event."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str


class SSEFormatter:
    """Utility class for formatting events into standard SSE protocol strings."""

    @staticmethod
    def format_event(event: str, data: Any) -> str:
        """
        Format an event name and JSON-serializable data dictionary or model into an SSE frame.
        Structure:
          event: <event>\n
          data: <json>\n\n
        """
        if isinstance(data, BaseModel):
            payload = data.model_dump_json()
        elif isinstance(data, (dict, list)):
            payload = json.dumps(data)
        else:
            payload = str(data)

        return f"event: {event}\ndata: {payload}\n\n"

    @classmethod
    def format_message_start(
        cls,
        message_id: UUID,
        conversation_id: UUID,
        sequence_number: int,
        role: str = "assistant",
    ) -> str:
        """Format the initial turn confirmation event."""
        data = SSEMessageStartData(
            message_id=message_id,
            conversation_id=conversation_id,
            role=role,
            sequence_number=sequence_number,
        )
        return cls.format_event("message_start", data)

    @classmethod
    def format_content_delta(cls, delta: str, index: int) -> str:
        """Format an incremental text delta token event."""
        data = SSEContentDeltaData(delta=delta, index=index)
        return cls.format_event("content_delta", data)

    @classmethod
    def format_message_complete(
        cls,
        message_id: UUID,
        conversation_id: UUID,
        finish_reason: str = "stop",
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> str:
        """Format the terminal turn completion event."""
        data = SSEMessageCompleteData(
            message_id=message_id,
            conversation_id=conversation_id,
            finish_reason=finish_reason,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        return cls.format_event("message_complete", data)

    @classmethod
    def format_error(cls, code: str, message: str) -> str:
        """Format a streaming error event."""
        data = SSEErrorData(code=code, message=message)
        return cls.format_event("error", data)

    @staticmethod
    def format_keepalive() -> str:
        """
        Format a keepalive comment.
        Lines starting with a colon (':') are standard SSE heartbeat comments
        and are ignored by SSE client parsers while keeping the TCP socket open.
        """
        return ": keepalive\n\n"
