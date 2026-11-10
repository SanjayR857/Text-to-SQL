"""
Protocols and structural typing contracts for conversation AI integrations.
"""
from collections.abc import AsyncIterator
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StreamChunk(BaseModel):
    """Atomic chunk emitted by the external AI generator during streaming."""

    model_config = ConfigDict(frozen=True)

    delta: str = Field(default="", description="Incremental text token delta")
    is_finish: bool = Field(default=False, description="True on final token stream termination")
    finish_reason: str | None = Field(
        default=None,
        description="Reason for termination (e.g. 'stop', 'length', 'content_filter')",
    )
    model_name: str | None = Field(default=None, description="Identifier of the executing model")
    prompt_tokens: int | None = Field(default=None, description="Token count for input prompt")
    completion_tokens: int | None = Field(
        default=None,
        description="Token count for generated completion",
    )


class ContextMessage(BaseModel):
    """Prior message representation passed in context assembly."""

    model_config = ConfigDict(frozen=True)

    role: str
    content: str
    sequence_number: int


class GenerationContext(BaseModel):
    """Historical context package assembled for the external generation engine."""

    model_config = ConfigDict(frozen=True)

    conversation_id: UUID
    user_id: UUID
    latest_summary: str | None = None
    messages: list[ContextMessage] = Field(
        default_factory=list,
        description="Chronological prior messages up to sequence N-1",
    )


class AIGeneratorProtocol(Protocol):
    """Interface that any downstream AI generation engine must implement."""

    async def generate_stream(
        self,
        context: GenerationContext,
        prompt: str,
    ) -> AsyncIterator[StreamChunk]:
        """Generate and yield streaming token chunks in response to user prompt."""
        ...


class TitleGeneratorProtocol(Protocol):
    """Interface for asynchronous conversation titling."""

    async def generate_title(
        self,
        user_prompt: str,
        assistant_response: str,
    ) -> str:
        """Generate a concise, contextual conversation title."""
        ...


class SummaryGeneratorProtocol(Protocol):
    """Interface for asynchronous conversation summarization."""

    async def generate_summary(
        self,
        existing_summary: str | None,
        new_messages: list[ContextMessage],
    ) -> str:
        """Generate or update a rolling summary from historical messages."""
        ...
