"""
Background embedding worker and schema synchronization processor.

Consumes SchemaChangeEvents to incrementally update, re-embed, or delete
table and column embeddings in pgvector upon database mutations.
"""
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncEngine
import structlog

from enterprise_ai_platform.text_to_sql.vector_store_interfaces import IVectorStore
from enterprise_ai_platform.text_to_sql.catalog import (
    EnterpriseMetadataCatalog,
)
from enterprise_ai_platform.text_to_sql.document_builder import (
    SchemaDocumentBuilder,
)
from enterprise_ai_platform.text_to_sql.schema_document import (
    SchemaDocument,
    SchemaDocumentType,
)
from enterprise_ai_platform.text_to_sql.schema_events import (
    SchemaChangeEvent,
    SchemaChangeType,
)
from enterprise_ai_platform.core.database import (
    get_async_engine,
)
from enterprise_ai_platform.text_to_sql.introspector import (
    PostgresSchemaIntrospector,
)

logger = structlog.get_logger(__name__)


class SchemaEmbeddingWorker:
    """
    Worker coordinating event-driven schema re-embedding into pgvector.

    Reacts to SchemaChangeEvents (CREATED, ALTERED, DROPPED, REFRESH_ALL)
    to keep vector store embeddings strictly synchronized with live PostgreSQL schemas.
    """

    def __init__(
        self,
        vector_store: IVectorStore,
        introspector: PostgresSchemaIntrospector | None = None,
        document_builder: SchemaDocumentBuilder | None = None,
        catalog: EnterpriseMetadataCatalog | None = None,
        engine: AsyncEngine | None = None,
    ) -> None:
        """
        Initialize schema embedding worker.

        Args:
            vector_store: Target vector store adapter (SchemaVectorStore).
            introspector: PostgresSchemaIntrospector instance.
            document_builder: SchemaDocumentBuilder instance.
            catalog: EnterpriseMetadataCatalog instance.
            engine: SQLAlchemy AsyncEngine.
        """
        self._vector_store = vector_store
        self._introspector = introspector or PostgresSchemaIntrospector()
        self._builder = document_builder or SchemaDocumentBuilder()
        self._catalog = catalog or EnterpriseMetadataCatalog()
        self._engine = engine

    def _get_engine(self) -> AsyncEngine:
        """Retrieve configured engine or fallback to connection manager singleton."""
        return self._engine or get_async_engine()

    async def handle_schema_change(self, event: SchemaChangeEvent) -> int:
        """
        Handle a SchemaChangeEvent by synchronizing affected table embeddings.

        Args:
            event: Domain SchemaChangeEvent.

        Returns:
            Number of documents upserted or removed.
        """
        logger.info(
            "Processing schema change event",
            event_id=str(event.event_id),
            change_type=event.change_type.value,
            affected_tables=event.affected_tables,
        )

        if event.change_type == SchemaChangeType.DROPPED:
            return await self._handle_dropped_tables(event)

        if event.change_type in (SchemaChangeType.CREATED, SchemaChangeType.ALTERED):
            return await self._handle_upsert_tables(
                event=event,
                target_tables=event.affected_tables,
            )

        if event.change_type == SchemaChangeType.REFRESH_ALL:
            return await self._handle_upsert_tables(
                event=event,
                target_tables=None,  # Introspect everything
            )

        return 0

    async def _handle_dropped_tables(self, event: SchemaChangeEvent) -> int:
        """
        Remove obsolete table and column documents when tables are dropped.
        """
        if not event.affected_tables:
            return 0

        # Retrieve existing document IDs from vector store to find column docs
        existing_hashes = await self._vector_store.get_document_hashes()
        dropped_lower = {t.strip().lower() for t in event.affected_tables}

        doc_ids_to_delete: list[str] = []
        for doc_id in existing_hashes.keys():
            # Document ID format: database:schema:table[:column]:TYPE
            parts = doc_id.split(":")
            if len(parts) >= 4:
                tbl_part = parts[2].lower()
                if tbl_part in dropped_lower:
                    doc_ids_to_delete.append(doc_id)

        if doc_ids_to_delete:
            deleted = await self._vector_store.delete_documents(doc_ids_to_delete)
            logger.info("Deleted stale schema documents", count=deleted)
            return deleted
        return 0

    async def _handle_upsert_tables(
        self,
        event: SchemaChangeEvent,
        target_tables: Sequence[str] | None,
    ) -> int:
        """
        Introspect, enrich, and upsert documents for new or modified tables.
        """
        engine = self._get_engine()

        # 1. Introspect live database structure
        raw_schema = await self._introspector.introspect_async(
            engine_or_conn=engine,
            database_id=event.database_id,
            schema_name=event.schema_name,
            target_tables=target_tables,
        )

        # 2. Enrich with business descriptions and synonyms
        enriched_schema = self._catalog.enrich_schema(raw_schema)

        # 3. Build semantic documents
        documents: list[SchemaDocument] = self._builder.build_documents_for_schema(
            schema=enriched_schema,
            include_columns=True,
        )

        # 4. Idempotent upsert into pgvector
        upserted_count = await self._vector_store.upsert_documents(documents)
        logger.info(
            "Completed schema embeddings sync",
            total_documents=len(documents),
            updated_count=upserted_count,
        )
        return upserted_count

    async def sync_all_schemas(
        self,
        database_id: str = "default",
        schema_name: str = "public",
    ) -> int:
        """
        Trigger full manual synchronization of all tables in the database.

        Args:
            database_id: Database identifier.
            schema_name: PostgreSQL schema name.

        Returns:
            Number of newly embedded or modified documents.
        """
        event = SchemaChangeEvent(
            database_id=database_id,
            schema_name=schema_name,
            change_type=SchemaChangeType.REFRESH_ALL,
            affected_tables=[],
        )
        return await self.handle_schema_change(event)
