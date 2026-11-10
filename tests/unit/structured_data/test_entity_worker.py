"""
Unit tests for EntityEmbeddingWorker.

Verifies:
    1. Safe template formatting for entity labels.
    2. Extraction of entity documents from database rows with physical column resolution.
    3. Table and batch synchronization with EntityVectorStore.
    4. Purging of deleted / orphaned entity rows.
    5. SchemaChangeEvent handling for entity dimension tables.
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

from enterprise_ai_platform.domain.structured_data import (
    ColumnMetadataEntity,
    DatabaseSchemaEntity,
    DEFAULT_ENTITY_TABLE_CONFIGS,
    EntityTableConfig,
    EntityValueDocument,
    SchemaChangeEvent,
    SchemaChangeType,
    TableMetadataEntity,
)
from enterprise_ai_platform.workers.entity_worker import (
    EntityEmbeddingWorker,
    _safe_format,
)


@pytest.fixture
def sample_project_schema() -> DatabaseSchemaEntity:
    """Fixture providing DatabaseSchemaEntity for ProjectName."""
    cols = {
        "id": ColumnMetadataEntity(name="id", data_type="VARCHAR(255)", is_primary_key=True),
        "projectname": ColumnMetadataEntity(name="projectName", data_type="VARCHAR(255)"),
        "verticalcode": ColumnMetadataEntity(name="verticalCode", data_type="VARCHAR(5)"),
        "pricingmodel": ColumnMetadataEntity(name="pricingModel", data_type="VARCHAR(50)"),
    }
    table = TableMetadataEntity(
        name="ProjectName",
        columns=cols,
        primary_keys=["id"],
    )
    return DatabaseSchemaEntity(
        database_id="default",
        schema_name="public",
        tables={"projectname": table},
    )


class TestEntityEmbeddingWorker:
    """Tests for EntityEmbeddingWorker functionality."""

    def test_safe_format_exact_and_case_insensitive(self) -> None:
        """_safe_format handles exact, case-insensitive, and missing keys."""
        template = "{projectName} (ID: {id})"
        assert _safe_format(template, {"projectName": "Apollo", "id": "PRJ-001"}) == "Apollo (ID: PRJ-001)"
        assert _safe_format(template, {"projectname": "Apollo", "ID": "PRJ-001"}) == "Apollo (ID: PRJ-001)"
        assert _safe_format(template, {"id": "PRJ-001"}) == "(ID: PRJ-001)"
        assert _safe_format("{missing}", {}) == "Unnamed Entity"

    @pytest.mark.asyncio
    async def test_extract_entities_unconfigured_table_raises(self) -> None:
        """Extracting from unconfigured table raises ValueError."""
        mock_store = MagicMock()
        worker = EntityEmbeddingWorker(vector_store=mock_store)

        with pytest.raises(ValueError, match="not configured for entity extraction"):
            await worker.extract_entities_from_table("NonExistentTable")

    @pytest.mark.asyncio
    async def test_extract_entities_table_not_in_db_returns_empty(self) -> None:
        """Returns empty list if table exists in config but not introspected in DB."""
        mock_store = MagicMock()
        mock_introspector = MagicMock()
        mock_introspector.introspect_async = AsyncMock(
            return_value=DatabaseSchemaEntity(database_id="default", schema_name="public", tables={})
        )
        mock_engine = MagicMock()

        worker = EntityEmbeddingWorker(
            vector_store=mock_store,
            introspector=mock_introspector,
            engine=mock_engine,
        )

        docs = await worker.extract_entities_from_table("ProjectName")
        assert docs == []

    @pytest.mark.asyncio
    async def test_extract_entities_success(
        self, sample_project_schema: DatabaseSchemaEntity
    ) -> None:
        """Extracts valid EntityValueDocuments from database rows."""
        mock_store = MagicMock()
        mock_introspector = MagicMock()
        mock_introspector.introspect_async = AsyncMock(return_value=sample_project_schema)

        # Mock DB query results
        mock_row1 = {
            "id": "PRJ-001",
            "projectName": "Apollo Platform",
            "verticalCode": "CHAIO",
            "pricingModel": "Fixed Price",
        }
        mock_row2 = {
            "id": "PRJ-002",
            "projectName": "Mercury Migration",
            "verticalCode": "CHFIO",
            "pricingModel": "Time and Material",
        }

        mock_mapping_result = MagicMock()
        mock_mapping_result.all.return_value = [mock_row1, mock_row2]

        mock_exec_result = MagicMock()
        mock_exec_result.mappings.return_value = mock_mapping_result

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value=mock_exec_result)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_ctx

        worker = EntityEmbeddingWorker(
            vector_store=mock_store,
            introspector=mock_introspector,
            engine=mock_engine,
        )

        docs = await worker.extract_entities_from_table("ProjectName")

        assert len(docs) == 2
        assert docs[0].primary_key_value == "PRJ-001"
        assert docs[0].entity_label == "Apollo Platform (ID: PRJ-001)"
        assert "Apollo Platform" in docs[0].searchable_text
        assert docs[0].metadata["vertical_code"] == "CHAIO"
        assert docs[0].metadata["project_id"] == "PRJ-001"

        assert docs[1].primary_key_value == "PRJ-002"
        assert docs[1].entity_label == "Mercury Migration (ID: PRJ-002)"

    @pytest.mark.asyncio
    async def test_sync_table_batches_and_upserts(self) -> None:
        """sync_table extracts rows and calls vector_store.upsert_entities in chunks."""
        mock_store = MagicMock()
        mock_store.upsert_entities = AsyncMock(return_value=2)

        worker = EntityEmbeddingWorker(vector_store=mock_store)

        sample_docs = [
            EntityValueDocument.create(
                table_name="ProjectName",
                primary_key_column="id",
                primary_key_value=f"PRJ-{i}",
                entity_label=f"Project {i}",
                searchable_text=f"Text {i}",
            )
            for i in range(5)
        ]

        worker.extract_entities_from_table = AsyncMock(return_value=sample_docs)  # type: ignore[method-assign]

        count = await worker.sync_table("ProjectName", batch_size=2)

        # 5 items with batch_size 2 -> 3 chunks (2, 2, 1)
        assert mock_store.upsert_entities.await_count == 3
        assert count == 6  # 3 batches * 2 returned each

    @pytest.mark.asyncio
    async def test_sync_all_entities(self) -> None:
        """sync_all_entities loops through all registered entity configs."""
        mock_store = MagicMock()
        worker = EntityEmbeddingWorker(vector_store=mock_store)
        worker.sync_table = AsyncMock(return_value=10)  # type: ignore[method-assign]

        results = await worker.sync_all_entities()

        assert "ProjectName" in results
        assert "Vertical" in results
        assert "EmployeeInformation" in results
        assert all(count == 10 for count in results.values())

    @pytest.mark.asyncio
    async def test_sync_deleted_entities_purges_orphans(
        self, sample_project_schema: DatabaseSchemaEntity
    ) -> None:
        """sync_deleted_entities finds IDs absent in live DB and calls delete_entities."""
        mock_store = MagicMock()
        mock_store.delete_entities = AsyncMock(return_value=1)

        mock_introspector = MagicMock()
        mock_introspector.introspect_async = AsyncMock(return_value=sample_project_schema)

        # Live DB has only PRJ-001
        mock_res1 = MagicMock()
        mock_res1.fetchall.return_value = [("PRJ-001",)]

        # Vector store has PRJ-001 and PRJ-002 (PRJ-002 is orphaned)
        mock_record_keep = MagicMock()
        mock_record_keep.document_id = "default:public:projectname:prj-001:ENTITY"
        mock_record_keep.primary_key_value = "PRJ-001"

        mock_record_orphan = MagicMock()
        mock_record_orphan.document_id = "default:public:projectname:prj-002:ENTITY"
        mock_record_orphan.primary_key_value = "PRJ-002"

        mock_res2 = MagicMock()
        mock_res2.all.return_value = [mock_record_keep, mock_record_orphan]

        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(side_effect=[mock_res1, mock_res2])

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.connect.return_value = mock_ctx

        worker = EntityEmbeddingWorker(
            vector_store=mock_store,
            introspector=mock_introspector,
            engine=mock_engine,
        )

        deleted = await worker.sync_deleted_entities("ProjectName")

        assert deleted == 1
        mock_store.delete_entities.assert_awaited_once_with(["default:public:projectname:prj-002:ENTITY"])

    @pytest.mark.asyncio
    async def test_handle_schema_change_dropped(self) -> None:
        """SchemaChangeEvent DROPPED purges table embeddings."""
        mock_store = MagicMock()
        mock_res = MagicMock()
        mock_res.rowcount = 5
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value=mock_res)

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_conn
        mock_engine = MagicMock()
        mock_engine.begin.return_value = mock_ctx

        worker = EntityEmbeddingWorker(vector_store=mock_store, engine=mock_engine)

        event = SchemaChangeEvent(
            event_id=uuid4(),
            change_type=SchemaChangeType.DROPPED,
            affected_tables=["ProjectName"],
        )

        deleted = await worker.handle_schema_change(event)
        assert deleted == 5

    @pytest.mark.asyncio
    async def test_handle_schema_change_altered(self) -> None:
        """SchemaChangeEvent ALTERED triggers re-sync of affected entity table."""
        mock_store = MagicMock()
        worker = EntityEmbeddingWorker(vector_store=mock_store)
        worker.sync_table = AsyncMock(return_value=3)  # type: ignore[method-assign]

        event = SchemaChangeEvent(
            event_id=uuid4(),
            change_type=SchemaChangeType.ALTERED,
            affected_tables=["Vertical"],
        )

        updated = await worker.handle_schema_change(event)
        assert updated == 3
        worker.sync_table.assert_awaited_once_with(
            table_name="Vertical",
            database_id="default",
            schema_name="public",
        )
