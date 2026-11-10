"""
pgvector-backed schema vector store and LlamaIndex retriever adapter.

Implements IVectorStore using PostgreSQL pgvector, AzureOpenAIEmbeddings,
and provides native LlamaIndex BaseRetriever integration.
"""
from datetime import datetime, timezone
from typing import Any, Sequence

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine

from text_to_sql.vector_store.vector_store_interfaces import (
    IVectorStore,
    VectorSearchResult,
)
from text_to_sql.vector_store.schema_document import (
    SchemaDocument,
    SchemaDocumentType,
)
from models.text_to_sql import (
    SchemaEmbeddingModel,
)
from providers.embeddings import AzureOpenAIEmbeddings


class SchemaVectorStore(IVectorStore):
    """
    Production-grade pgvector storage adapter for table and column schema embeddings.

    Features:
        - Azure OpenAI text-embedding-3-small (1536 dimensions).
        - Idempotent upserts via SHA-256 content hashes (skips unchanged embeddings).
        - PostgreSQL native ON CONFLICT upserting.
        - Exact metadata filtering by document_type and table_name.
    """

    def __init__(
        self,
        engine: AsyncEngine,
        embeddings: AzureOpenAIEmbeddings | None = None,
    ) -> None:
        """
        Initialize vector store adapter.

        Args:
            engine: SQLAlchemy AsyncEngine connected to PostgreSQL.
            embeddings: AzureOpenAIEmbeddings provider.
        """
        self._engine = engine
        self._embeddings = embeddings or AzureOpenAIEmbeddings()

    async def get_document_hashes(self) -> dict[str, str]:
        """
        Retrieve mapping of document_id to content_hash from PostgreSQL.
        """
        async with self._engine.connect() as conn:
            stmt = select(
                SchemaEmbeddingModel.document_id,
                SchemaEmbeddingModel.content_hash,
            )
            result = await conn.execute(stmt)
            return {row.document_id: row.content_hash for row in result.all()}

    async def upsert_documents(
        self,
        documents: list[SchemaDocument],
    ) -> int:
        """
        Upsert schema documents into pgvector with hash-based idempotency.

        Skips documents whose content_hash has not changed, saving API costs and latency.
        """
        if not documents:
            return 0

        # 1. Fetch existing hashes for idempotency check
        existing_hashes = await self.get_document_hashes()

        # 2. Filter for changed or new documents
        changed_docs: list[SchemaDocument] = [
            doc
            for doc in documents
            if existing_hashes.get(doc.document_id) != doc.content_hash
        ]

        if not changed_docs:
            return 0

        # 3. Generate embeddings in batch
        texts_to_embed = [doc.searchable_text for doc in changed_docs]
        embeddings = await self._embeddings.embed_batch(texts_to_embed)

        # 4. Perform PostgreSQL atomic upsert
        now = datetime.now(timezone.utc)
        async with self._engine.begin() as conn:
            for doc, emb in zip(changed_docs, embeddings):
                values = {
                    "document_id": doc.document_id,
                    "document_type": doc.document_type.value,
                    "database_id": doc.database_id,
                    "schema_name": doc.schema_name,
                    "table_name": doc.table_name,
                    "column_name": doc.column_name,
                    "searchable_text": doc.searchable_text,
                    "description": doc.description,
                    "metadata": doc.metadata,
                    "content_hash": doc.content_hash,
                    "schema_version": doc.schema_version,
                    "embedding": emb,
                    "updated_at": now,
                }

                table_target = SchemaEmbeddingModel.__table__
                insert_stmt = pg_insert(table_target).values(**values)
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[table_target.c.document_id],
                    set_={
                        "searchable_text": insert_stmt.excluded.searchable_text,
                        "description": insert_stmt.excluded.description,
                        "metadata": insert_stmt.excluded.metadata,
                        "content_hash": insert_stmt.excluded.content_hash,
                        "schema_version": insert_stmt.excluded.schema_version,
                        "embedding": insert_stmt.excluded.embedding,
                        "updated_at": now,
                    },
                )
                await conn.execute(upsert_stmt)

        return len(changed_docs)

    async def delete_documents(
        self,
        document_ids: list[str],
    ) -> int:
        """
        Delete documents by deterministic IDs.
        """
        if not document_ids:
            return 0

        async with self._engine.begin() as conn:
            stmt = delete(SchemaEmbeddingModel).where(
                SchemaEmbeddingModel.document_id.in_(document_ids)
            )
            result = await conn.execute(stmt)
            return result.rowcount

    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        document_type: SchemaDocumentType | None = None,
        table_name: str | None = None,
    ) -> list[VectorSearchResult]:
        """
        Execute cosine similarity search against pgvector schema embeddings.
        """
        # 1. Generate query vector
        query_vector = await self._embeddings.embed_query(query)

        # 2. Build similarity query using cosine distance
        cosine_dist = SchemaEmbeddingModel.embedding.cosine_distance(query_vector)
        stmt = (
            select(
                SchemaEmbeddingModel,
                (1.0 - cosine_dist).label("similarity_score"),
            )
            .order_by(cosine_dist)
            .limit(top_k)
        )

        if document_type is not None:
            stmt = stmt.where(SchemaEmbeddingModel.document_type == document_type.value)

        if table_name is not None:
            stmt = stmt.where(
                func.lower(SchemaEmbeddingModel.table_name) == table_name.strip().lower()
            )

        async with self._engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.all()

        results: list[VectorSearchResult] = []
        for row in rows:
            model: SchemaEmbeddingModel = row[0]
            score: float = float(row[1])

            results.append(
                VectorSearchResult(
                    document_id=model.document_id,
                    document_type=SchemaDocumentType(model.document_type),
                    table_name=model.table_name,
                    column_name=model.column_name,
                    searchable_text=model.searchable_text,
                    description=model.description,
                    score=score,
                    metadata=model.metadata_,
                )
            )

        return results

    def as_llamaindex_retriever(
        self,
        top_k: int = 5,
        document_type: SchemaDocumentType | None = None,
    ) -> BaseRetriever:
        """
        Create a LlamaIndex-compatible BaseRetriever wrapping this vector store.

        Args:
            top_k: Number of schema nodes to retrieve.
            document_type: Optional filter for TABLE or COLUMN nodes.

        Returns:
            LlamaIndex BaseRetriever instance.
        """
        return SchemaLlamaIndexRetriever(
            vector_store=self,
            top_k=top_k,
            document_type=document_type,
        )


class SchemaLlamaIndexRetriever(BaseRetriever):
    """
    LlamaIndex BaseRetriever implementation dispatching to SchemaVectorStore.
    """

    def __init__(
        self,
        vector_store: SchemaVectorStore,
        top_k: int = 5,
        document_type: SchemaDocumentType | None = None,
    ) -> None:
        """
        Initialize LlamaIndex retriever wrapper.

        Args:
            vector_store: Target SchemaVectorStore instance.
            top_k: Top K results to fetch.
            document_type: Granularity filter.
        """
        super().__init__()
        self._vector_store = vector_store
        self._top_k = top_k
        self._document_type = document_type

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """Synchronous retrieval fallback (raises NotImplementedError to enforce async)."""
        raise NotImplementedError("Use aretrieve for asynchronous schema retrieval")

    async def _aretrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """
        Asynchronously retrieve schema nodes via vector similarity.
        """
        results = await self._vector_store.similarity_search(
            query=query_bundle.query_str,
            top_k=self._top_k,
            document_type=self._document_type,
        )

        nodes: list[NodeWithScore] = []
        for r in results:
            node = TextNode(
                id_=r.document_id,
                text=r.searchable_text,
                metadata={
                    "table_name": r.table_name,
                    "column_name": r.column_name,
                    "document_type": r.document_type.value,
                    "description": r.description,
                    **r.metadata,
                },
            )
            nodes.append(NodeWithScore(node=node, score=r.score))

        return nodes
