"""
Abstract schema retriever port.

Defines the contract for retrieving authorized schema representations for Text-to-SQL generation.
"""
from abc import ABC, abstractmethod

from rbac.access_context import (
    ResolvedAccessContext,
)


class ISchemaRetriever(ABC):
    """
    Port for retrieving authorized schema context for a natural language user query.
    """

    @abstractmethod
    async def retrieve_authorized_schema(
        self,
        query: str,
        access_context: ResolvedAccessContext,
        top_k_tables: int = 5,
    ) -> str:
        """
        Retrieve and project authorized database schema for an LLM prompt.

        Args:
            query: Natural language user question.
            access_context: Authenticated user's resolved authorization context.
            top_k_tables: Number of candidate tables to retrieve.

        Returns:
            Clean markdown-formatted schema with approved join hints.
        """
        pass
