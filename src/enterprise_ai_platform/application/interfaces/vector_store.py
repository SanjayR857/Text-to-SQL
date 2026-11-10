"""
Abstract vector store port and data structures.

Defines the contract for storing, querying, and deleting dense vector embeddings
(e.g., pgvector, Azure AI Search).
"""
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VectorDocument(BaseModel):
    """Document chunk packaged with its vector representation and metadata."""

    model_config = ConfigDict(frozen=True)

    id: str | UUID
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorSearchResult(BaseModel):
    """Result hit returned from a vector similarity search."""

    model_config = ConfigDict(frozen=True)

    id: str | UUID
    content: str
    score: float = Field(description="Similarity score (cosine similarity or inner product)")
    metadata: dict[str, Any] = Field(default_factory=dict)


class VectorStoreProtocol(Protocol):
    """Protocol for vector indexing and approximate nearest-neighbor (ANN) retrieval."""

    async def add_documents(self, documents: list[VectorDocument]) -> list[str]:
        """Index a list of documents and embeddings into the vector store."""
        ...

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Query the vector store for top_k most similar document chunks."""
        ...

    async def delete_documents(self, document_ids: list[str]) -> bool:
        """Remove documents from the vector store by identifiers."""
        ...
