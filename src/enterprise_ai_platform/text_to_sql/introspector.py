"""
PostgreSQL schema introspector adapter using SQLAlchemy.

Extracts live database structure, table definitions, column types, nullability,
primary key constraints, foreign key relationships, and indexes.
"""
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from sqlalchemy import Connection, inspect
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from enterprise_ai_platform.text_to_sql.schema import (
    DatabaseSchemaEntity,
)
from enterprise_ai_platform.text_to_sql.metadata import (
    ColumnMetadataEntity,
    ForeignKeyRelation,
    TableMetadataEntity,
)

DEFAULT_IGNORED_TABLES: frozenset[str] = frozenset({"alembic_version"})


class PostgresSchemaIntrospector:
    """
    SQLAlchemy-based introspector extracting physical schema metadata from PostgreSQL.

    Supports asynchronous inspection via AsyncEngine/AsyncConnection through run_sync,
    as well as synchronous inspection for background workers and testing.
    """

    def __init__(
        self,
        ignored_tables: set[str] | frozenset[str] | None = None,
    ) -> None:
        """
        Initialize introspector with optional table exclusion list.

        Args:
            ignored_tables: Set of table names to ignore during introspection.
        """
        self._ignored_tables = (
            frozenset(t.lower() for t in ignored_tables)
            if ignored_tables is not None
            else DEFAULT_IGNORED_TABLES
        )

    async def introspect_async(
        self,
        engine_or_conn: AsyncEngine | AsyncConnection,
        database_id: str = "default",
        schema_name: str = "public",
        target_tables: Sequence[str] | None = None,
        version: str = "1.0.0",
    ) -> DatabaseSchemaEntity:
        """
        Asynchronously introspect database schema using SQLAlchemy 2.0 run_sync.

        Args:
            engine_or_conn: SQLAlchemy AsyncEngine or active AsyncConnection.
            database_id: Logical database identifier.
            schema_name: Target PostgreSQL schema name (default: 'public').
            target_tables: Optional subset of table names to introspect.
            version: Schema version string.

        Returns:
            Canonical DatabaseSchemaEntity populated with physical database facts.
        """
        sync_fn: Callable[[Connection], DatabaseSchemaEntity] = (
            lambda sync_conn: self.introspect_sync(
                conn=sync_conn,
                database_id=database_id,
                schema_name=schema_name,
                target_tables=target_tables,
                version=version,
            )
        )

        if isinstance(engine_or_conn, AsyncEngine):
            async with engine_or_conn.connect() as conn:
                return await conn.run_sync(sync_fn)
        else:
            return await engine_or_conn.run_sync(sync_fn)

    def introspect_sync(
        self,
        conn: Connection,
        database_id: str = "default",
        schema_name: str = "public",
        target_tables: Sequence[str] | None = None,
        version: str = "1.0.0",
    ) -> DatabaseSchemaEntity:
        """
        Synchronously introspect database schema using a SQLAlchemy Connection.

        Args:
            conn: Active synchronous SQLAlchemy Connection.
            database_id: Logical database identifier.
            schema_name: Target PostgreSQL schema name (default: 'public').
            target_tables: Optional subset of table names to introspect.
            version: Schema version string.

        Returns:
            Canonical DatabaseSchemaEntity populated with physical database facts.
        """
        inspector: Inspector = inspect(conn)
        available_tables = inspector.get_table_names(schema=schema_name)

        target_set: set[str] | None = None
        if target_tables is not None:
            target_set = {t.strip().lower() for t in target_tables}

        tables_map: dict[str, TableMetadataEntity] = {}

        for tbl_name in available_tables:
            tbl_lower = tbl_name.strip().lower()

            # Skip ignored or non-targeted tables
            if tbl_lower in self._ignored_tables:
                continue
            if target_set is not None and tbl_lower not in target_set:
                continue

            table_entity = self._introspect_table(
                inspector=inspector,
                table_name=tbl_name,
                schema_name=schema_name,
                database_id=database_id,
            )
            tables_map[tbl_lower] = table_entity

        return DatabaseSchemaEntity(
            database_id=database_id,
            schema_name=schema_name,
            version=version,
            tables=tables_map,
            last_introspected_at=datetime.now(timezone.utc),
            description=f"Introspected schema for database '{database_id}', schema '{schema_name}'",
        )

    def _introspect_table(
        self,
        inspector: Inspector,
        table_name: str,
        schema_name: str,
        database_id: str,
    ) -> TableMetadataEntity:
        """
        Introspect a single table's columns, primary keys, foreign keys, and indexes.

        Args:
            inspector: SQLAlchemy Inspector instance.
            table_name: Table name.
            schema_name: PostgreSQL schema name.
            database_id: Logical database identifier.

        Returns:
            TableMetadataEntity representing physical table structure.
        """
        # 1. Primary keys
        pk_constraint = inspector.get_pk_constraint(table_name, schema=schema_name)
        pk_cols = pk_constraint.get("constrained_columns") or []
        pk_set = {c.strip().lower() for c in pk_cols}

        # 2. Foreign keys
        fk_specs = inspector.get_foreign_keys(table_name, schema=schema_name)
        foreign_keys: list[ForeignKeyRelation] = []
        fk_col_targets: dict[str, str] = {}

        for fk in fk_specs:
            constrained = fk.get("constrained_columns") or []
            ref_table = fk.get("referred_table") or ""
            ref_schema = fk.get("referred_schema") or schema_name
            ref_cols = fk.get("referred_columns") or []

            foreign_keys.append(
                ForeignKeyRelation(
                    constrained_columns=constrained,
                    referred_schema=ref_schema,
                    referred_table=ref_table,
                    referred_columns=ref_cols,
                )
            )

            # Map single-column FKs to 'TargetTable.targetColumn'
            if len(constrained) == 1 and len(ref_cols) == 1:
                fk_col_targets[constrained[0].strip().lower()] = f"{ref_table}.{ref_cols[0]}"

        # 3. Indexes
        indexes = inspector.get_indexes(table_name, schema=schema_name)
        index_names = [
            idx["name"] for idx in indexes if idx.get("name") is not None
        ]

        # 4. Columns
        raw_columns = inspector.get_columns(table_name, schema=schema_name)
        columns_map: dict[str, ColumnMetadataEntity] = {}

        for col in raw_columns:
            col_name = str(col["name"])
            col_lower = col_name.strip().lower()
            data_type = str(col["type"])
            is_nullable = bool(col.get("nullable", True))
            is_pk = col_lower in pk_set
            is_fk = col_lower in fk_col_targets
            fk_target = fk_col_targets.get(col_lower)

            columns_map[col_lower] = ColumnMetadataEntity(
                name=col_name,
                data_type=data_type,
                is_nullable=is_nullable,
                is_primary_key=is_pk,
                is_foreign_key=is_fk,
                foreign_key_target=fk_target,
            )

        return TableMetadataEntity(
            name=table_name,
            schema_name=schema_name,
            database_id=database_id,
            columns=columns_map,
            primary_keys=pk_cols,
            foreign_keys=foreign_keys,
            indexes=index_names,
        )
