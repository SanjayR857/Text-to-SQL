"""
Pydantic v2 schemas for Message Feedback endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackSubmitRequest(BaseModel):
    """Payload for submitting or updating message evaluation feedback."""

    model_config = ConfigDict(extra="forbid")

    rating: int = Field(
        ge=1,
        le=5,
        description="Rating from 1 (Poor / Thumbs Down) to 5 (Excellent / Thumbs Up)",
    )
    comment: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional qualitative commentary",
    )


class FeedbackResponse(BaseModel):
    """Serialized representation of message feedback."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_id: UUID
    conversation_id: UUID
    user_id: UUID
    rating: int
    comment: str | None
    created_at: datetime
