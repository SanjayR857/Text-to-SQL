"""
Unit tests for SchemaVectorStore and SchemaLlamaIndexRetriever.

Verifies:
    1. Idempotent upserting using SHA-256 hash comparison.
    2. Similarity search dispatch and score mapping.
    3. Document deletion by ID.
    4. LlamaIndex BaseRetriever wrapper and TextNode construction.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from llama_index.core.schema import NodeWithScore, QueryBundle

from text_to_sql.vector_store_interfaces import (
    VectorSearchResult,
)
from text_to_sql import (
    SchemaDocument,
    SchemaDocumentType,
)
from text_to_sql.models import (
    SchemaEmbeddingModel,
)
from text_to_sql.schema_vector_store import (
    SchemaLlamaIndexRetriever,
    SchemaVectorStore,
)


@pytest.fixture
def sample_table_doc() -> SchemaDocument:
    """Fixture providing a valid table SchemaDocument."""
    return SchemaDocument.create_table_document(
        table_name="EmployeeInformation",
        searchable_text="Table EmployeeInformation stores profiles.",
        description="Employee profiles.",
    )


class TestSchemaVectorStore:
    """Tests for SchemaVectorStore operations and idempotency."""

    @pytest.mark.asyncio
    async def test_upsert_skips_unchanged_documents(
        self, sample_table_doc: SchemaDocument
    ) -> None:
        """Documents with matching content_hash are skipped during upsert."""
        mock_engine = MagicMock()
        mock_embeddings = MagicMock()
        mock_embeddings.embed_batch = AsyncMock()

        store = SchemaVectorStore(engine=mock_engine, embeddings=mock_embeddings)
        # Mock get_document_hashes returning existing identical hash
        store.get_document_hashes = AsyncMock(  # type: ignore[method-assign]
            return_value={sample_table_doc.document_id: sample_table_doc.content_hash}
        )

        upserted_count = await store.upsert_documents([sample_table_doc])

        assert upserted_count == 0
        mock_embeddings.embed_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_embeds_and_saves_new_or_changed_documents(
        self, sample_table_doc: SchemaDocument
    ) -> None:
        """New or changed documents trigger embedding generation and PostgreSQL upsert."""
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock()

        # Mock engine.begin() async context manager
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_ctx

        dummy_vector = [0.1] * 1536
        mock_embeddings = MagicMock()
        mock_embeddings.embed_batch = AsyncMock(return_value=[dummy_vector])

        store = SchemaVectorStore(engine=mock_engine, embeddings=mock_embeddings)
        store.get_document_hashes = AsyncMock(return_value={})  # type: ignore[method-assign]

        upserted_count = await store.upsert_documents([sample_table_doc])

        assert upserted_count == 1
        mock_embeddings.embed_batch.assert_awaited_once_with([sample_table_doc.searchable_text])
        mock_conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_documents(self) -> None:
        """delete_documents removes records matching specified document IDs."""
        mock_result = MagicMock()
        mock_result.rowcount = 2

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_ctx

        store = SchemaVectorStore(engine=mock_engine, embeddings=MagicMock())
        deleted_count = await store.delete_documents(["id1", "id2"])

        assert deleted_count == 2
        mock_conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_similarity_search_returns_ranked_results(self) -> None:
        """similarity_search embeds query and formats results as VectorSearchResult."""
        dummy_vector = [0.05] * 1536
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query = AsyncMock(return_value=dummy_vector)

        mock_model = MagicMock(spec=SchemaEmbeddingModel)
        mock_model.document_id = "default:public:employeeinformation:TABLE"
        mock_model.document_type = "TABLE"
        mock_model.table_name = "EmployeeInformation"
        mock_model.column_name = None
        mock_model.searchable_text = "Search text"
        mock_model.description = "Employee info"
        mock_model.metadata_ = {"schema_name": "public"}

        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_model, 0.92)]

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value=mock_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_ctx

        store = SchemaVectorStore(engine=mock_engine, embeddings=mock_embeddings)
        results = await store.similarity_search("find employee directory", top_k=1)

        assert len(results) == 1
        r = results[0]
        assert isinstance(r, VectorSearchResult)
        assert r.document_id == "default:public:employeeinformation:TABLE"
        assert r.document_type == SchemaDocumentType.TABLE
        assert r.table_name == "EmployeeInformation"
        assert r.score == 0.92


class TestSchemaLlamaIndexRetriever:
    """Tests for LlamaIndex BaseRetriever integration."""

    @pytest.mark.asyncio
    async def test_as_llamaindex_retriever_aretrieve(self) -> None:
        """LlamaIndex retriever returns NodeWithScore objects with TextNodes."""
        mock_store = MagicMock(spec=SchemaVectorStore)
        mock_store.similarity_search = AsyncMock(
            return_value=[
                VectorSearchResult(
                    document_id="default:public:projectname:TABLE",
                    document_type=SchemaDocumentType.TABLE,
                    table_name="ProjectName",
                    column_name=None,
                    searchable_text="Table ProjectName",
                    description="Projects",
                    score=0.88,
                    metadata={"vertical": "AIO"},
                )
            ]
        )

        retriever = SchemaLlamaIndexRetriever(vector_store=mock_store, top_k=3)
        nodes = await retriever.aretrieve(QueryBundle(query_str="show all projects"))

        assert len(nodes) == 1
        node_with_score = nodes[0]
        assert isinstance(node_with_score, NodeWithScore)
        assert node_with_score.score == 0.88
        assert node_with_score.node.id_ == "default:public:projectname:TABLE"
        assert node_with_score.node.text == "Table ProjectName"
        assert node_with_score.node.metadata["table_name"] == "ProjectName"
        assert node_with_score.node.metadata["vertical"] == "AIO"
