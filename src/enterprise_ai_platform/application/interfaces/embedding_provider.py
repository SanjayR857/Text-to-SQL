"""
Abstract embedding provider port.

Defines the contract for dense text embedding generation used by Document RAG,
semantic chunking, and vector databases.
"""
from typing import Protocol


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
