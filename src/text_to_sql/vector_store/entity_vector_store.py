"""
pgvector-backed entity vector store and LlamaIndex retriever adapter.

Stores and queries selective entity value embeddings (projects, verticals, employees)
with PostgreSQL ON CONFLICT upserting, SHA-256 idempotency, and RBAC pre-filtering.
"""
from datetime import datetime, timezone
from typing import Any, Sequence

from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode
from sqlalchemy import delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine

from rbac.access_context import (
    ResolvedAccessContext,
)
from text_to_sql.vector_store.entity_document import (
    EntityMatchResult,
    EntityValueDocument,
)
from models.text_to_sql import (
    EntityEmbeddingModel,
)
from providers.embeddings import AzureOpenAIEmbeddings


class EntityVectorStore:
    """
    pgvector storage adapter for selective entity value embeddings.

    Enables semantic entity resolution and exact WHERE clause value matching
    with strict caller authorization pre-filtering.
    """

    def __init__(
        self,
        engine: AsyncEngine,
        embeddings: AzureOpenAIEmbeddings | None = None,
    ) -> None:
        """
        Initialize entity vector store.

        Args:
            engine: SQLAlchemy AsyncEngine connected to PostgreSQL.
            embeddings: AzureOpenAIEmbeddings provider.
        """
        self._engine = engine
        self._embeddings = embeddings or AzureOpenAIEmbeddings()

    async def get_entity_hashes(self) -> dict[str, str]:
        """
        Retrieve mapping of document_id to content_hash from entity_embeddings table.
        """
        async with self._engine.connect() as conn:
            stmt = select(
                EntityEmbeddingModel.document_id,
                EntityEmbeddingModel.content_hash,
            )
            result = await conn.execute(stmt)
            return {row.document_id: row.content_hash for row in result.all()}

    async def upsert_entities(
        self,
        entities: list[EntityValueDocument],
    ) -> int:
        """
        Upsert entity value documents with hash-based change detection.

        Skips entities whose content_hash has not changed.
        """
        if not entities:
            return 0

        existing_hashes = await self.get_entity_hashes()
        changed = [e for e in entities if existing_hashes.get(e.document_id) != e.content_hash]
        if not changed:
            return 0

        # Generate embeddings in batch
        texts = [e.searchable_text for e in changed]
        embeddings = await self._embeddings.embed_batch(texts)

        table_target = EntityEmbeddingModel.__table__
        now = datetime.now(timezone.utc)

        async with self._engine.begin() as conn:
            for entity, emb in zip(changed, embeddings):
                values = {
                    "document_id": entity.document_id,
                    "database_id": entity.database_id,
                    "schema_name": entity.schema_name,
                    "table_name": entity.table_name,
                    "primary_key_column": entity.primary_key_column,
                    "primary_key_value": entity.primary_key_value,
                    "entity_label": entity.entity_label,
                    "searchable_text": entity.searchable_text,
                    "metadata": entity.metadata,
                    "content_hash": entity.content_hash,
                    "embedding": emb,
                    "updated_at": now,
                }

                insert_stmt = pg_insert(table_target).values(**values)
                upsert_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[table_target.c.document_id],
                    set_={
                        "entity_label": insert_stmt.excluded.entity_label,
                        "searchable_text": insert_stmt.excluded.searchable_text,
                        "metadata": insert_stmt.excluded.metadata,
                        "content_hash": insert_stmt.excluded.content_hash,
                        "embedding": insert_stmt.excluded.embedding,
                        "updated_at": now,
                    },
                )
                await conn.execute(upsert_stmt)

        return len(changed)

    async def delete_entities(self, document_ids: list[str]) -> int:
        """
        Delete entities by deterministic document IDs.
        """
        if not document_ids:
            return 0

        async with self._engine.begin() as conn:
            stmt = delete(EntityEmbeddingModel).where(
                EntityEmbeddingModel.document_id.in_(document_ids)
            )
            result = await conn.execute(stmt)
            return result.rowcount

    async def search_entities(
        self,
        query: str,
        access_context: ResolvedAccessContext | None = None,
        table_names: Sequence[str] | None = None,
        top_k: int = 5,
        score_threshold: float = 0.65,
    ) -> list[EntityMatchResult]:
        """
        Execute cosine similarity search for entity values with RBAC filtering.

        Args:
            query: Natural language user question or entity term.
            access_context: Optional resolved access context to restrict results.
            table_names: Optional list of table names to restrict entity search.
            top_k: Maximum entity matches to return.
            score_threshold: Minimum cosine similarity score threshold (0.0 to 1.0).

        Returns:
            Ranked list of EntityMatchResult items.
        """
        query_vector = await self._embeddings.embed_query(query)
        cosine_dist = EntityEmbeddingModel.embedding.cosine_distance(query_vector)

        stmt = (
            select(
                EntityEmbeddingModel,
                (1.0 - cosine_dist).label("similarity_score"),
            )
            .order_by(cosine_dist)
            .limit(top_k)
        )

        # 1. Filter by target tables
        if table_names:
            tables_lower = [t.strip().lower() for t in table_names]
            stmt = stmt.where(func.lower(EntityEmbeddingModel.table_name).in_(tables_lower))

        # 2. RBAC Scope Pre-Filtering
        if access_context is not None:
            # If caller is not CA Admin, apply access restrictions
            allowed_tables_lower = {t.lower() for t in access_context.allowed_tables}
            stmt = stmt.where(func.lower(EntityEmbeddingModel.table_name).in_(allowed_tables_lower))

        async with self._engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.all()

        matches: list[EntityMatchResult] = []
        for row in rows:
            model: EntityEmbeddingModel = row[0]
            score: float = float(row[1])

            if score < score_threshold:
                continue

            matches.append(
                EntityMatchResult(
                    table_name=model.table_name,
                    primary_key_column=model.primary_key_column,
                    primary_key_value=model.primary_key_value,
                    entity_label=model.entity_label,
                    score=score,
                    matched_text=model.searchable_text,
                    metadata=model.metadata_,
                )
            )

        return matches

    def as_llamaindex_retriever(
        self,
        top_k: int = 5,
        table_names: Sequence[str] | None = None,
    ) -> BaseRetriever:
        """
        Create a LlamaIndex-compatible BaseRetriever for entity value lookup.
        """
        return EntityLlamaIndexRetriever(
            vector_store=self,
            top_k=top_k,
            table_names=table_names,
        )


class EntityLlamaIndexRetriever(BaseRetriever):
    """
    LlamaIndex BaseRetriever wrapping EntityVectorStore.
    """

    def __init__(
        self,
        vector_store: EntityVectorStore,
        top_k: int = 5,
        table_names: Sequence[str] | None = None,
    ) -> None:
        super().__init__()
        self._vector_store = vector_store
        self._top_k = top_k
        self._table_names = table_names

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        raise NotImplementedError("Use aretrieve for asynchronous entity retrieval")

    async def _aretrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        matches = await self._vector_store.search_entities(
            query=query_bundle.query_str,
            table_names=self._table_names,
            top_k=self._top_k,
        )

        nodes: list[NodeWithScore] = []
        for m in matches:
            node = TextNode(
                id_=f"{m.table_name}:{m.primary_key_value}",
                text=m.matched_text,
                metadata={
                    "table_name": m.table_name,
                    "primary_key_column": m.primary_key_column,
                    "primary_key_value": m.primary_key_value,
                    "entity_label": m.entity_label,
                    **m.metadata,
                },
            )
            nodes.append(NodeWithScore(node=node, score=m.score))

        return nodes
