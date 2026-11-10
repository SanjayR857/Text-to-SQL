"""
Abstract LLM and Embedding provider interfaces and data structures.
"""
from collections.abc import AsyncIterator
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from chat.protocols import GenerationContext, StreamChunk


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


class EmbeddingProviderProtocol(Protocol):
    """Protocol for generating vector embeddings from text strings."""

    async def embed_text(self, text: str) -> list[float]:
        """Generate a dense vector for a single text segment."""
        ...

    async def embed_query(self, query: str) -> list[float]:
        """Generate an embedding vector optimized for search queries."""
        ...

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
        """Generate embedding vectors for a batch of text segments."""
        ...

    def embed_text_sync(self, text: str) -> list[float]:
        """Synchronously generate an embedding vector for offline indexing tasks."""
        ...

    def embed_batch_sync(
        self,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
        """Synchronously generate embedding vectors for offline batch ingestion."""
        ...
