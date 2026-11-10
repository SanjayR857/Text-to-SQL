"""
Abstract LLM provider contracts and data structures.

Defines protocols for chat completion, structured model generation, and real-time streaming.
"""
from collections.abc import AsyncIterator
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai_platform.domain.conversations.protocols import (
    GenerationContext,
    StreamChunk,
)


class ChatMessage(BaseModel):
    """Normalized chat message structure across LLM providers."""

    model_config = ConfigDict(frozen=True)

    role: str = Field(description="Role identifier: 'system', 'user', or 'assistant'")
    content: str = Field(description="Message text payload")
    name: str | None = Field(default=None, description="Optional participant name")


class LLMCompletionResponse(BaseModel):
    """Complete, non-streaming LLM generation response."""

    model_config = ConfigDict(frozen=True)

    content: str
    model_name: str
    finish_reason: str = "stop"
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMProviderProtocol(Protocol):
    """Abstract interface defining chat completion and streaming capabilities."""

    async def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMCompletionResponse:
        """Execute a complete chat completion request."""
        ...

    async def generate_stream(
        self,
        context: GenerationContext,
        prompt: str,
    ) -> AsyncIterator[StreamChunk]:
        """Stream token chunks in response to dialogue context and user prompt."""
        ...
