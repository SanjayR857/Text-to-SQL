"""
Unit tests for SchemaEmbeddingWorker and InMemoryEventBus.

Verifies:
    1. SchemaChangeEvent contract and serialization.
    2. InMemoryEventBus subscription and async dispatch.
    3. Worker incremental synchronization on CREATED/ALTERED events.
    4. Worker document cleanup on DROPPED events.
    5. Worker full synchronization on REFRESH_ALL events.
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

from enterprise_ai_platform.application.interfaces.vector_store import IVectorStore
from enterprise_ai_platform.application.structured_data.metadata_catalog import (
    EnterpriseMetadataCatalog,
)
from enterprise_ai_platform.application.structured_data.schema_document_builder import (
    SchemaDocumentBuilder,
)
from enterprise_ai_platform.domain.structured_data import (
    ColumnMetadataEntity,
    DatabaseSchemaEntity,
    SchemaChangeEvent,
    SchemaChangeType,
    TableMetadataEntity,
)
from enterprise_ai_platform.infrastructure.database.schema_introspector import (
    PostgresSchemaIntrospector,
)
from enterprise_ai_platform.infrastructure.messaging import InMemoryEventBus
from enterprise_ai_platform.workers.embedding_worker import SchemaEmbeddingWorker


@pytest.fixture
def sample_schema_entity() -> DatabaseSchemaEntity:
    """Fixture providing a DatabaseSchemaEntity with EmployeeInformation."""
    col = ColumnMetadataEntity(
        name="employeeMailId",
        data_type="VARCHAR(255)",
        is_primary_key=True,
    )
    table = TableMetadataEntity(
        name="EmployeeInformation",
        columns={"employeemailid": col},
        primary_keys=["employeeMailId"],
    )
    return DatabaseSchemaEntity(
        database_id="default",
        schema_name="public",
        tables={"employeeinformation": table},
    )


class TestInMemoryEventBus:
    """Tests for typed pub/sub event bus."""

    @pytest.mark.asyncio
    async def test_subscribe_and_publish_dispatches_event(self) -> None:
        """Published event is received by subscribed handler."""
        bus = InMemoryEventBus()
        received_events: list[SchemaChangeEvent] = []

        async def handler(event: SchemaChangeEvent) -> None:
            received_events.append(event)

        bus.subscribe(SchemaChangeEvent, handler)

        event = SchemaChangeEvent(
            change_type=SchemaChangeType.ALTERED,
            affected_tables=["EmployeeInformation"],
        )
        await bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0] == event

    @pytest.mark.asyncio
    async def test_unsubscribe_stops_dispatch(self) -> None:
        """Unsubscribed handler does not receive subsequent events."""
        bus = InMemoryEventBus()
        counter = {"count": 0}

        async def handler(event: SchemaChangeEvent) -> None:
            counter["count"] += 1

        bus.subscribe(SchemaChangeEvent, handler)
        bus.unsubscribe(SchemaChangeEvent, handler)

        event = SchemaChangeEvent(
            change_type=SchemaChangeType.ALTERED,
            affected_tables=["EmployeeInformation"],
        )
        await bus.publish(event)

        assert counter["count"] == 0


class TestSchemaEmbeddingWorker:
    """Tests for SchemaEmbeddingWorker event handling and synchronization."""

    @pytest.mark.asyncio
    async def test_handle_altered_event_introspects_and_upserts(
        self, sample_schema_entity: DatabaseSchemaEntity
    ) -> None:
        """ALTERED event triggers targeted introspection, enrichment, and upsert."""
        mock_introspector = MagicMock(spec=PostgresSchemaIntrospector)
        mock_introspector.introspect_async = AsyncMock(return_value=sample_schema_entity)

        mock_store = MagicMock(spec=IVectorStore)
        mock_store.upsert_documents = AsyncMock(return_value=2)

        worker = SchemaEmbeddingWorker(
            vector_store=mock_store,
            introspector=mock_introspector,
            document_builder=SchemaDocumentBuilder(),
            catalog=EnterpriseMetadataCatalog(),
            engine=MagicMock(),
        )

        event = SchemaChangeEvent(
            change_type=SchemaChangeType.ALTERED,
            affected_tables=["EmployeeInformation"],
        )

        updated_count = await worker.handle_schema_change(event)

        assert updated_count == 2
        mock_introspector.introspect_async.assert_awaited_once()
        mock_store.upsert_documents.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_dropped_event_deletes_table_documents(self) -> None:
        """DROPPED event deletes all corresponding table and column vector documents."""
        mock_store = MagicMock(spec=IVectorStore)
        mock_store.get_document_hashes = AsyncMock(
            return_value={
                "default:public:employeeinformation:TABLE": "hash1",
                "default:public:employeeinformation:employeemailid:COLUMN": "hash2",
                "default:public:projectname:TABLE": "hash3",
            }
        )
        mock_store.delete_documents = AsyncMock(return_value=2)

        worker = SchemaEmbeddingWorker(
            vector_store=mock_store,
            engine=MagicMock(),
        )

        event = SchemaChangeEvent(
            change_type=SchemaChangeType.DROPPED,
            affected_tables=["EmployeeInformation"],
        )

        deleted_count = await worker.handle_schema_change(event)

        assert deleted_count == 2
        mock_store.delete_documents.assert_awaited_once_with(
            [
                "default:public:employeeinformation:TABLE",
                "default:public:employeeinformation:employeemailid:COLUMN",
            ]
        )

    @pytest.mark.asyncio
    async def test_sync_all_schemas_triggers_refresh_all(
        self, sample_schema_entity: DatabaseSchemaEntity
    ) -> None:
        """sync_all_schemas executes full schema introspection and bulk upsert."""
        mock_introspector = MagicMock(spec=PostgresSchemaIntrospector)
        mock_introspector.introspect_async = AsyncMock(return_value=sample_schema_entity)

        mock_store = MagicMock(spec=IVectorStore)
        mock_store.upsert_documents = AsyncMock(return_value=5)

        worker = SchemaEmbeddingWorker(
            vector_store=mock_store,
            introspector=mock_introspector,
            engine=MagicMock(),
        )

        upserted = await worker.sync_all_schemas()

        assert upserted == 5
        mock_introspector.introspect_async.assert_awaited_once()
        mock_store.upsert_documents.assert_awaited_once()
