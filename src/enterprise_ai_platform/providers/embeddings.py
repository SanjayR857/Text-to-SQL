"""
Azure OpenAI vector embeddings implementation using text-embedding-3-small.

Generates dense 1536-dimensional vector representations for semantic search,
RAG document chunking, and pgvector database storage.
"""
from openai import AsyncAzureOpenAI, AzureOpenAI
import structlog

from enterprise_ai_platform.core.config import get_settings
from enterprise_ai_platform.core.telemetry import trace_span
from enterprise_ai_platform.providers.azure_openai_client import (
    get_azure_openai_client,
    get_sync_azure_openai_client,
)

logger = structlog.get_logger(__name__)


class AzureOpenAIEmbeddings:
    """
    Embedding generation service using Azure OpenAI text-embedding-3-small.
    Produces 1536-dimensional normalized vectors.
    """

    def __init__(
        self,
        client: AsyncAzureOpenAI | None = None,
        sync_client: AzureOpenAI | None = None,
        deployment_name: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        settings = get_settings()
        self.client = client
        self.sync_client = sync_client
        self.deployment_name = (
            deployment_name or settings.azure_openai_embedding_deployment
        )
        self.dimensions = dimensions or settings.embedding_dimensions

    def _get_async_client(self) -> AsyncAzureOpenAI:
        return self.client or get_azure_openai_client()

    def _get_sync_client(self) -> AzureOpenAI:
        return self.sync_client or get_sync_azure_openai_client()

    @trace_span("azure_openai.embed_text")
    async def embed_text(self, text: str) -> list[float]:
        """Generate a dense embedding vector for a single text string."""
        results = await self.embed_batch([text])
        return results[0]

    @trace_span("azure_openai.embed_query")
    async def embed_query(self, query: str) -> list[float]:
        """Generate an embedding vector for a search query."""
        clean_query = query.strip().replace("\n", " ")
        return await self.embed_text(clean_query)

    @trace_span("azure_openai.embed_batch")
    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
        """
        Generate embedding vectors for a batch of strings, chunking requests to prevent timeouts.
        """
        if not texts:
            return []

        client = self._get_async_client()
        all_embeddings: list[list[float]] = []

        # Sanitize texts (replace newlines as recommended by OpenAI)
        sanitized = [t.replace("\n", " ").strip() or " " for t in texts]

        for i in range(0, len(sanitized), batch_size):
            chunk = sanitized[i : i + batch_size]
            try:
                response = await client.embeddings.create(
                    input=chunk,
                    model=self.deployment_name,
                )
                batch_results = [item.embedding for item in response.data]
                all_embeddings.extend(batch_results)
            except Exception as exc:
                logger.error(
                    "Azure OpenAI embedding batch failed",
                    batch_offset=i,
                    batch_size=len(chunk),
                    error=str(exc),
                )
                raise

        return all_embeddings

    def embed_text_sync(self, text: str) -> list[float]:
        """Synchronously generate an embedding vector for offline indexing workers."""
        client = self._get_sync_client()
        clean = text.replace("\n", " ").strip() or " "
        response = client.embeddings.create(
            input=[clean],
            model=self.deployment_name,
        )
        return response.data[0].embedding

    def embed_batch_sync(
        self,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
        """Synchronously generate embeddings for a batch of texts."""
        if not texts:
            return []

        client = self._get_sync_client()
        all_embeddings: list[list[float]] = []
        sanitized = [t.replace("\n", " ").strip() or " " for t in texts]

        for i in range(0, len(sanitized), batch_size):
            chunk = sanitized[i : i + batch_size]
            response = client.embeddings.create(
                input=chunk,
                model=self.deployment_name,
            )
            all_embeddings.extend([item.embedding for item in response.data])

        return all_embeddings
