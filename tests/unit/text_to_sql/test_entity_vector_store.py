"""
Unit tests for EntityVectorStore and EntityLlamaIndexRetriever.

Verifies:
    1. Idempotent upserting using SHA-256 hash comparison.
    2. Cosine similarity search and score threshold filtering.
    3. Document deletion by ID.
    4. LlamaIndex BaseRetriever wrapper for entity retrieval.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from llama_index.core.schema import NodeWithScore, QueryBundle

from text_to_sql import (
    EntityMatchResult,
    EntityValueDocument,
)
from text_to_sql.models import (
    EntityEmbeddingModel,
)
from text_to_sql.entity_vector_store import (
    EntityLlamaIndexRetriever,
    EntityVectorStore,
)


@pytest.fixture
def sample_entity_doc() -> EntityValueDocument:
    """Fixture providing a valid EntityValueDocument."""
    return EntityValueDocument.create(
        table_name="ProjectName",
        primary_key_column="id",
        primary_key_value="PRJ-001",
        entity_label="Apollo AI Migration (ID: PRJ-001)",
        searchable_text="Project: Apollo AI Migration (ID: PRJ-001)",
        vertical_code="CHAIO",
        project_id="PRJ-001",
    )


class TestEntityVectorStore:
    """Tests for EntityVectorStore operations and idempotency."""

    @pytest.mark.asyncio
    async def test_upsert_skips_unchanged_entities(
        self, sample_entity_doc: EntityValueDocument
    ) -> None:
        """Entities with matching content_hash are skipped during upsert."""
        mock_engine = MagicMock()
        mock_embeddings = MagicMock()
        mock_embeddings.embed_batch = AsyncMock()

        store = EntityVectorStore(engine=mock_engine, embeddings=mock_embeddings)
        store.get_entity_hashes = AsyncMock(  # type: ignore[method-assign]
            return_value={sample_entity_doc.document_id: sample_entity_doc.content_hash}
        )

        upserted_count = await store.upsert_entities([sample_entity_doc])

        assert upserted_count == 0
        mock_embeddings.embed_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_embeds_and_saves_new_entities(
        self, sample_entity_doc: EntityValueDocument
    ) -> None:
        """New or modified entities trigger embedding and upsert."""
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_ctx

        dummy_vector = [0.05] * 1536
        mock_embeddings = MagicMock()
        mock_embeddings.embed_batch = AsyncMock(return_value=[dummy_vector])

        store = EntityVectorStore(engine=mock_engine, embeddings=mock_embeddings)
        store.get_entity_hashes = AsyncMock(return_value={})  # type: ignore[method-assign]

        upserted_count = await store.upsert_entities([sample_entity_doc])

        assert upserted_count == 1
        mock_embeddings.embed_batch.assert_awaited_once_with([sample_entity_doc.searchable_text])
        mock_conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_entities(self) -> None:
        """delete_entities removes records by document ID."""
        mock_result = MagicMock()
        mock_result.rowcount = 1

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_ctx

        store = EntityVectorStore(engine=mock_engine, embeddings=MagicMock())
        deleted = await store.delete_entities(["id1"])

        assert deleted == 1
        mock_conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_search_entities_returns_matches(self) -> None:
        """search_entities returns EntityMatchResult items exceeding threshold."""
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query = AsyncMock(return_value=[0.1] * 1536)

        mock_model = MagicMock(spec=EntityEmbeddingModel)
        mock_model.table_name = "ProjectName"
        mock_model.primary_key_column = "id"
        mock_model.primary_key_value = "PRJ-001"
        mock_model.entity_label = "Apollo AI Migration (ID: PRJ-001)"
        mock_model.searchable_text = "Project: Apollo AI Migration"
        mock_model.metadata_ = {"vertical_code": "CHAIO"}

        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_model, 0.89)]

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_ctx

        store = EntityVectorStore(engine=mock_engine, embeddings=mock_embeddings)
        matches = await store.search_entities("Apollo project", score_threshold=0.6)

        assert len(matches) == 1
        m = matches[0]
        assert isinstance(m, EntityMatchResult)
        assert m.table_name == "ProjectName"
        assert m.primary_key_value == "PRJ-001"
        assert m.score == 0.89


class TestEntityLlamaIndexRetriever:
    """Tests for LlamaIndex BaseRetriever entity integration."""

    @pytest.mark.asyncio
    async def test_as_llamaindex_retriever_aretrieve(self) -> None:
        """LlamaIndex entity retriever returns NodeWithScore objects."""
        mock_store = MagicMock(spec=EntityVectorStore)
        mock_store.search_entities = AsyncMock(
            return_value=[
                EntityMatchResult(
                    table_name="ProjectName",
                    primary_key_column="id",
                    primary_key_value="PRJ-001",
                    entity_label="Apollo (ID: PRJ-001)",
                    score=0.91,
                    matched_text="Apollo project",
                    metadata={"vertical_code": "CHAIO"},
                )
            ]
        )

        retriever = EntityLlamaIndexRetriever(vector_store=mock_store, top_k=2)
        nodes = await retriever.aretrieve(QueryBundle(query_str="Apollo"))

        assert len(nodes) == 1
        node = nodes[0]
        assert isinstance(node, NodeWithScore)
        assert node.score == 0.91
        assert node.node.metadata["primary_key_value"] == "PRJ-001"
