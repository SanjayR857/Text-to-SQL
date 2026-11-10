"""
Background entity value ingestion worker and row-level embedding synchronizer.

Extracts selective entity rows from enterprise dimension/lookup tables (e.g. ProjectName,
Vertical, EmployeeInformation) and maintains dense pgvector embeddings with SHA-256
hash idempotency and RBAC pre-filtering metadata.
"""
from __future__ import annotations

import re
from typing import Any, Sequence

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine
import structlog

from enterprise_ai_platform.text_to_sql.entity_document import (
    DEFAULT_ENTITY_TABLE_CONFIGS,
    EntityTableConfig,
    EntityValueDocument,
)
from enterprise_ai_platform.text_to_sql.schema_events import (
    SchemaChangeEvent,
    SchemaChangeType,
)
from enterprise_ai_platform.text_to_sql.metadata import TableMetadataEntity
from enterprise_ai_platform.core.database import (
    get_async_engine,
)
from enterprise_ai_platform.text_to_sql.models import (
    EntityEmbeddingModel,
)
from enterprise_ai_platform.text_to_sql.introspector import (
    PostgresSchemaIntrospector,
)
from enterprise_ai_platform.text_to_sql.entity_vector_store import (
    EntityVectorStore,
)

logger = structlog.get_logger(__name__)


def _get_row_value(row: dict[str, Any], col_name: str) -> Any:
    """Safely get value from row dict with case-insensitive fallback."""
    if col_name in row:
        return row[col_name]
    col_lower = col_name.lower()
    for k, v in row.items():
        if k.lower() == col_lower:
            return v
    return None


def _safe_format(template: str, values: dict[str, Any]) -> str:
    """
    Safely format a string template with a dictionary, ignoring missing keys.
    """
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        val = values.get(key)
        if val is None:
            # Case-insensitive lookup fallback
            for k, v in values.items():
                if k.lower() == key.lower():
                    val = v
                    break
        return str(val) if val is not None else ""

    result = re.sub(r"\{(\w+)\}", replacer, template).strip()
    return result if result else "Unnamed Entity"


class EntityEmbeddingWorker:
    """
    Worker coordinating selective row-level entity value ingestion into pgvector.

    Features:
        - Selective extraction restricted to whitelisted dimension tables.
        - Case-resilient column resolution via live table introspection.
        - Structured metadata injection (vertical_code, project_id, owner_email) for RBAC pre-filtering.
        - Batched embedding generation with SHA-256 change detection.
        - Stale entity deletion and schema change event reaction.
    """

    def __init__(
        self,
        vector_store: EntityVectorStore,
        introspector: PostgresSchemaIntrospector | None = None,
        configs: dict[str, EntityTableConfig] | None = None,
        engine: AsyncEngine | None = None,
    ) -> None:
        """
        Initialize entity embedding worker.

        Args:
            vector_store: EntityVectorStore adapter.
            introspector: PostgresSchemaIntrospector instance.
            configs: Mapping of lower-case table names to EntityTableConfig.
            engine: SQLAlchemy AsyncEngine.
        """
        self._vector_store = vector_store
        self._introspector = introspector or PostgresSchemaIntrospector()
        self._configs = configs if configs is not None else DEFAULT_ENTITY_TABLE_CONFIGS
        self._engine = engine

    def _get_engine(self) -> AsyncEngine:
        """Retrieve configured engine or fallback to connection manager singleton."""
        return self._engine or get_async_engine()

    def get_table_config(self, table_name: str) -> EntityTableConfig | None:
        """
        Lookup EntityTableConfig case-insensitively.
        """
        return self._configs.get(table_name.strip().lower())

    async def extract_entities_from_table(
        self,
        table_name: str,
        database_id: str = "default",
        schema_name: str = "public",
    ) -> list[EntityValueDocument]:
        """
        Extract entity rows from a configured dimension table and build EntityValueDocuments.

        Args:
            table_name: Canonical or configured table name.
            database_id: Logical database identifier.
            schema_name: PostgreSQL schema name.

        Returns:
            List of validated EntityValueDocument objects ready for vector upsert.
        """
        config = self.get_table_config(table_name)
        if config is None:
            raise ValueError(f"Table '{table_name}' is not configured for entity extraction")

        engine = self._get_engine()

        # 1. Introspect live table to get physical column casing
        schema_entity = await self._introspector.introspect_async(
            engine_or_conn=engine,
            database_id=database_id,
            schema_name=schema_name,
            target_tables=[config.table_name],
        )

        table_meta = schema_entity.get_table(config.table_name)
        if table_meta is None:
            logger.warning("Target entity table not found in database", table_name=config.table_name)
            return []

        # 2. Resolve configured columns against physical columns
        physical_cols = {col_entity.name.lower(): col_entity.name for col_entity in table_meta.columns.values()}

        resolved_pk = physical_cols.get(config.primary_key_column.lower())
        if resolved_pk is None:
            # Fall back to introspected table primary key if available
            if table_meta.primary_key_columns:
                resolved_pk = table_meta.primary_key_columns[0]
            else:
                logger.error(
                    "Primary key column not found for entity table",
                    table=config.table_name,
                    expected_pk=config.primary_key_column,
                )
                return []

        # Resolve searchable columns
        resolved_search_cols: list[str] = []
        for col in config.searchable_columns:
            real_col = physical_cols.get(col.lower())
            if real_col and real_col not in resolved_search_cols:
                resolved_search_cols.append(real_col)

        if not resolved_search_cols:
            resolved_search_cols = [resolved_pk]

        # Resolve RBAC filter columns
        resolved_vertical_col = (
            physical_cols.get(config.vertical_code_column.lower())
            if config.vertical_code_column
            else None
        )
        resolved_project_col = (
            physical_cols.get(config.project_id_column.lower())
            if config.project_id_column
            else None
        )
        resolved_owner_col = (
            physical_cols.get(config.owner_email_column.lower())
            if config.owner_email_column
            else None
        )

        # Collect all columns to query
        all_query_cols = set(resolved_search_cols)
        all_query_cols.add(resolved_pk)
        if resolved_vertical_col:
            all_query_cols.add(resolved_vertical_col)
        if resolved_project_col:
            all_query_cols.add(resolved_project_col)
        if resolved_owner_col:
            all_query_cols.add(resolved_owner_col)

        quoted_cols = [f'"{col}"' for col in sorted(all_query_cols)]
        query_sql = f'SELECT {", ".join(quoted_cols)} FROM "{schema_name}"."{table_meta.name}"'

        # 3. Query rows from PostgreSQL
        async with engine.connect() as conn:
            result = await conn.execute(text(query_sql))
            rows = result.mappings().all()

        # 4. Convert rows to EntityValueDocuments
        documents: list[EntityValueDocument] = []
        for row in rows:
            row_dict = dict(row)
            pk_val = _get_row_value(row_dict, resolved_pk)
            if pk_val is None:
                continue
            pk_val_str = str(pk_val).strip()
            if not pk_val_str:
                continue

            # Format label
            entity_label = _safe_format(config.label_template, row_dict)
            if not entity_label or entity_label == "Unnamed Entity":
                entity_label = f"{table_meta.name} ({pk_val_str})"

            # Build semantic searchable text
            text_parts = [f"Table: {table_meta.name}"]
            for col in resolved_search_cols:
                val = _get_row_value(row_dict, col)
                if val is not None and str(val).strip():
                    text_parts.append(f"{col}: {val}")
            searchable_text = " | ".join(text_parts)

            # Metadata for RBAC pre-filtering
            v_val = _get_row_value(row_dict, resolved_vertical_col) if resolved_vertical_col else None
            vertical_code = str(v_val).strip() if v_val is not None else None

            p_val = _get_row_value(row_dict, resolved_project_col) if resolved_project_col else None
            project_id = str(p_val).strip() if p_val is not None else None

            o_val = _get_row_value(row_dict, resolved_owner_col) if resolved_owner_col else None
            owner_email = str(o_val).strip().lower() if o_val is not None else None

            doc = EntityValueDocument.create(
                table_name=table_meta.name,
                primary_key_column=resolved_pk,
                primary_key_value=pk_val_str,
                entity_label=entity_label,
                searchable_text=searchable_text,
                database_id=database_id,
                schema_name=schema_name,
                vertical_code=vertical_code,
                project_id=project_id,
                owner_email=owner_email,
            )
            documents.append(doc)

        logger.info(
            "Extracted entity documents",
            table_name=table_meta.name,
            total_extracted=len(documents),
        )
        return documents

    async def sync_table(
        self,
        table_name: str,
        database_id: str = "default",
        schema_name: str = "public",
        batch_size: int = 100,
    ) -> int:
        """
        Synchronize entity embeddings for a specific dimension table.

        Args:
            table_name: Target table name.
            database_id: Database identifier.
            schema_name: PostgreSQL schema name.
            batch_size: Batch size for vector store upsert.

        Returns:
            Number of newly inserted or updated entity embeddings.
        """
        documents = await self.extract_entities_from_table(
            table_name=table_name,
            database_id=database_id,
            schema_name=schema_name,
        )

        if not documents:
            return 0

        total_upserted = 0
        for i in range(0, len(documents), batch_size):
            chunk = documents[i : i + batch_size]
            count = await self._vector_store.upsert_entities(chunk)
            total_upserted += count

        logger.info(
            "Completed entity table synchronization",
            table_name=table_name,
            total_entities=len(documents),
            updated_entities=total_upserted,
        )
        return total_upserted

    async def sync_all_entities(
        self,
        database_id: str = "default",
        schema_name: str = "public",
        batch_size: int = 100,
    ) -> dict[str, int]:
        """
        Synchronize all configured dimension tables into pgvector.

        Returns:
            Mapping of table_name to count of updated entity embeddings.
        """
        results: dict[str, int] = {}
        for config_key, config in self._configs.items():
            try:
                count = await self.sync_table(
                    table_name=config.table_name,
                    database_id=database_id,
                    schema_name=schema_name,
                    batch_size=batch_size,
                )
                results[config.table_name] = count
            except Exception as e:
                logger.error(
                    "Failed to sync entity table",
                    table_name=config.table_name,
                    error=str(e),
                )
                results[config.table_name] = 0

        return results

    async def sync_deleted_entities(
        self,
        table_name: str,
        database_id: str = "default",
        schema_name: str = "public",
    ) -> int:
        """
        Purge orphaned entity embeddings whose source rows were deleted from PostgreSQL.

        Args:
            table_name: Table name to check.
            database_id: Database identifier.
            schema_name: PostgreSQL schema name.

        Returns:
            Number of orphaned entity embeddings deleted.
        """
        config = self.get_table_config(table_name)
        if config is None:
            return 0

        engine = self._get_engine()

        # 1. Get live PK values from physical table
        try:
            schema_entity = await self._introspector.introspect_async(
                engine_or_conn=engine,
                database_id=database_id,
                schema_name=schema_name,
                target_tables=[config.table_name],
            )
            table_meta = schema_entity.get_table(config.table_name)
            if table_meta is None:
                return 0

            physical_cols = {col_name.lower(): col_name for col_name in table_meta.columns.keys()}
            resolved_pk = physical_cols.get(config.primary_key_column.lower())
            if not resolved_pk:
                return 0

            query_sql = f'SELECT "{resolved_pk}" FROM "{schema_name}"."{table_meta.name}"'
            async with engine.connect() as conn:
                res = await conn.execute(text(query_sql))
                live_pks = {str(row[0]).strip().lower() for row in res.fetchall() if row[0] is not None}
        except Exception as e:
            logger.warning("Could not query live table PKs for deletion sync", error=str(e))
            return 0

        # 2. Get existing document IDs in entity_embeddings for this table
        canonical_tbl_lower = table_meta.name.lower()
        async with engine.connect() as conn:
            stmt = select(
                EntityEmbeddingModel.document_id,
                EntityEmbeddingModel.primary_key_value,
            ).where(
                func.lower(EntityEmbeddingModel.table_name) == canonical_tbl_lower
            )
            res = await conn.execute(stmt)
            existing_records = res.all()

        orphaned_ids: list[str] = [
            row.document_id
            for row in existing_records
            if row.primary_key_value.strip().lower() not in live_pks
        ]

        if orphaned_ids:
            deleted_count = await self._vector_store.delete_entities(orphaned_ids)
            logger.info("Purged orphaned entity embeddings", table=config.table_name, deleted=deleted_count)
            return deleted_count

        return 0

    async def handle_schema_change(self, event: SchemaChangeEvent) -> int:
        """
        React to SchemaChangeEvents to maintain entity embeddings consistency.

        Args:
            event: Domain SchemaChangeEvent.

        Returns:
            Number of updated or deleted records.
        """
        if event.change_type == SchemaChangeType.DROPPED:
            total_deleted = 0
            engine = self._get_engine()
            for dropped_table in event.affected_tables:
                cfg = self.get_table_config(dropped_table)
                if cfg is not None:
                    async with engine.begin() as conn:
                        stmt = delete(EntityEmbeddingModel).where(
                            func.lower(EntityEmbeddingModel.table_name) == cfg.table_name.lower()
                        )
                        res = await conn.execute(stmt)
                        total_deleted += res.rowcount
            return total_deleted

        if event.change_type in (SchemaChangeType.ALTERED, SchemaChangeType.CREATED):
            total_updated = 0
            for affected_table in event.affected_tables:
                cfg = self.get_table_config(affected_table)
                if cfg is not None:
                    updated = await self.sync_table(
                        table_name=cfg.table_name,
                        database_id=event.database_id,
                        schema_name=event.schema_name,
                    )
                    total_updated += updated
            return total_updated

        if event.change_type == SchemaChangeType.REFRESH_ALL:
            results = await self.sync_all_entities(
                database_id=event.database_id,
                schema_name=event.schema_name,
            )
            return sum(results.values())

        return 0
