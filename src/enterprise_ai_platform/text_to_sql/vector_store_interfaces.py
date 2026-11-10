"""
Abstract vector store port and search result contracts.

Defines the interface for schema document vector storage, similarity search,
and hash-based change detection.
"""
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai_platform.text_to_sql.schema_document import (
    SchemaDocument,
    SchemaDocumentType,
)


class VectorSearchResult(BaseModel):
    """
    Result item returned by vector similarity search.
    """

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(..., description="Unique document identifier")
    document_type: SchemaDocumentType = Field(..., description="Granularity (TABLE or COLUMN)")
    table_name: str = Field(..., description="Target physical table name")
    column_name: str | None = Field(default=None, description="Target column name if COLUMN type")
    searchable_text: str = Field(..., description="Searchable semantic text")
    description: str = Field(default="", description="Business description")
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class IVectorStore(ABC):
    """
    Port defining vector storage, similarity search, and synchronization operations.
    """

    @abstractmethod
    async def upsert_documents(
        self,
        documents: list[SchemaDocument],
    ) -> int:
        """
        Upsert schema documents into the vector store.

        Implementations should perform idempotent hashing checks to avoid
        re-embedding unchanged documents.

        Args:
            documents: List of SchemaDocument instances to ingest.

        Returns:
            Number of documents newly embedded or updated.
        """
        pass

    @abstractmethod
    async def delete_documents(
        self,
        document_ids: list[str],
    ) -> int:
        """
        Delete documents by deterministic document IDs.

        Args:
            document_ids: List of document IDs to remove.

        Returns:
            Number of documents removed.
        """
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        document_type: SchemaDocumentType | None = None,
        table_name: str | None = None,
    ) -> list[VectorSearchResult]:
        """
        Perform semantic similarity search against indexed schema documents.

        Args:
            query: Natural language search query or user prompt.
            top_k: Maximum number of results to return.
            document_type: Optional filter for TABLE or COLUMN granularity.
            table_name: Optional filter for a specific table.

        Returns:
            Ranked list of VectorSearchResult items ordered by similarity.
        """
        pass

    @abstractmethod
    async def get_document_hashes(self) -> dict[str, str]:
        """
        Retrieve mapping of document_id to content_hash for all stored documents.

        Used for diffing and change detection during schema synchronization.
        """
        pass
