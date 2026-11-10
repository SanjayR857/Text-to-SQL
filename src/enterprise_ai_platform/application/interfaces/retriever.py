"""
Abstract document retriever port.

Provides a unified interface for document retrieval across dense vector search,
hybrid BM25/keyword search, and reranking pipelines.
"""
from typing import Any, Protocol

from enterprise_ai_platform.application.interfaces.vector_store import (
    VectorSearchResult,
)


class RetrieverProtocol(Protocol):
    """High-level document search and retrieval protocol."""

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Retrieve the most relevant document chunks matching the query and filters."""
        ...
