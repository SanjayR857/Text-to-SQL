"""
Schema document builder service.

Transforms physical and hybrid schema entities into enriched table-level
and column-level SchemaDocument objects optimized for vector embedding.
"""
from typing import Any

from text_to_sql.schema.database_schema import (
    DatabaseSchemaEntity,
)
from text_to_sql.vector_store.schema_document import (
    SchemaDocument,
    SchemaDocumentType,
)
from text_to_sql.schema.metadata import (
    ColumnMetadataEntity,
    TableMetadataEntity,
)


class SchemaDocumentBuilder:
    """
    Constructs canonical SchemaDocument instances from schema metadata entities.

    Generates semantic search prose for table-level and column-level granularity,
    assigns deterministic IDs, and calculates SHA-256 content hashes.
    """

    def build_table_document(
        self,
        table: TableMetadataEntity,
        schema_name: str | None = None,
        database_id: str | None = None,
        schema_version: str = "1.0.0",
        extra_metadata: dict[str, Any] | None = None,
    ) -> SchemaDocument:
        """
        Build a table-level SchemaDocument encapsulating the table and its columns.

        Args:
            table: TableMetadataEntity to transform.
            schema_name: Optional override for schema name.
            database_id: Optional override for database identifier.
            schema_version: Schema version string.
            extra_metadata: Optional additional key-value metadata.

        Returns:
            Validated table-level SchemaDocument.
        """
        effective_db = (database_id or table.database_id).strip()
        effective_schema = (schema_name or table.schema_name).strip()

        # Format semantic text for embedding
        lines: list[str] = [
            f"Table: {effective_schema}.{table.name}",
        ]

        if table.description:
            lines.append(f"Description: {table.description}")

        if table.synonyms:
            lines.append(f"Synonyms: {', '.join(table.synonyms)}")

        if table.primary_keys:
            lines.append(f"Primary Keys: {', '.join(table.primary_keys)}")

        if table.foreign_keys:
            fk_summaries: list[str] = []
            for fk in table.foreign_keys:
                cols = ", ".join(fk.constrained_columns)
                target = f"{fk.referred_table}({', '.join(fk.referred_columns)})"
                fk_summaries.append(f"{cols} -> {target}")
            lines.append(f"Foreign Key Relationships: {'; '.join(fk_summaries)}")

        lines.append("Columns:")
        for col_name in table.list_column_names():
            col = table.get_column(col_name)
            if col is None:
                continue

            null_status = "NULL" if col.is_nullable else "NOT NULL"
            col_line = f"- {col.name} ({col.data_type}, {null_status})"

            tags: list[str] = []
            if col.is_primary_key:
                tags.append("PK")
            if col.is_foreign_key:
                tags.append(f"FK -> {col.foreign_key_target or 'Unknown'}")
            if tags:
                col_line += f" [{', '.join(tags)}]"

            if col.description:
                col_line += f": {col.description}"
            if col.synonyms:
                col_line += f" (Synonyms: {', '.join(col.synonyms)})"

            lines.append(col_line)

        searchable_text = "\n".join(lines)

        metadata: dict[str, Any] = {
            "columns_count": len(table.columns),
            "primary_keys": list(table.primary_keys),
            "has_foreign_keys": bool(table.foreign_keys),
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        return SchemaDocument.create_table_document(
            table_name=table.name,
            searchable_text=searchable_text,
            description=table.description or "",
            database_id=effective_db,
            schema_name=effective_schema,
            schema_version=schema_version,
            extra_metadata=metadata,
        )

    def build_column_document(
        self,
        table: TableMetadataEntity,
        column: ColumnMetadataEntity,
        schema_name: str | None = None,
        database_id: str | None = None,
        schema_version: str = "1.0.0",
        extra_metadata: dict[str, Any] | None = None,
    ) -> SchemaDocument:
        """
        Build a column-level SchemaDocument encapsulating an individual column.

        Args:
            table: Parent TableMetadataEntity.
            column: Target ColumnMetadataEntity.
            schema_name: Optional override for schema name.
            database_id: Optional override for database identifier.
            schema_version: Schema version string.
            extra_metadata: Optional additional key-value metadata.

        Returns:
            Validated column-level SchemaDocument.
        """
        effective_db = (database_id or table.database_id).strip()
        effective_schema = (schema_name or table.schema_name).strip()

        lines: list[str] = [
            f"Column: {column.name}",
            f"Table: {effective_schema}.{table.name}",
            f"Data Type: {column.data_type} ({'NULL' if column.is_nullable else 'NOT NULL'})",
        ]

        # Key constraints
        if column.is_primary_key:
            lines.append("Key Role: Primary Key")
        elif column.is_foreign_key:
            target_str = column.foreign_key_target or "referenced table"
            lines.append(f"Key Role: Foreign Key referencing {target_str}")
        else:
            lines.append("Key Role: Standard Column")

        if column.description:
            lines.append(f"Description: {column.description}")

        if column.synonyms:
            lines.append(f"Synonyms: {', '.join(column.synonyms)}")

        if column.sample_values:
            lines.append(f"Sample Values: {', '.join(column.sample_values)}")

        if column.sensitivity:
            lines.append(f"Sensitivity: {column.sensitivity}")

        if table.description:
            lines.append(f"Parent Table Purpose: {table.description}")

        searchable_text = "\n".join(lines)

        metadata: dict[str, Any] = {
            "is_nullable": column.is_nullable,
            "is_primary_key": column.is_primary_key,
            "is_foreign_key": column.is_foreign_key,
            "foreign_key_target": column.foreign_key_target,
            "sensitivity": column.sensitivity,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        return SchemaDocument.create_column_document(
            table_name=table.name,
            column_name=column.name,
            searchable_text=searchable_text,
            description=column.description or "",
            database_id=effective_db,
            schema_name=effective_schema,
            schema_version=schema_version,
            data_type=column.data_type,
            extra_metadata=metadata,
        )

    def build_documents_for_table(
        self,
        table: TableMetadataEntity,
        include_columns: bool = True,
        schema_name: str | None = None,
        database_id: str | None = None,
        schema_version: str = "1.0.0",
    ) -> list[SchemaDocument]:
        """
        Generate all schema documents (table-level and optionally column-level) for a table.

        Args:
            table: Target TableMetadataEntity.
            include_columns: Whether to generate individual column documents.
            schema_name: Optional override for schema name.
            database_id: Optional override for database identifier.
            schema_version: Schema version string.

        Returns:
            List of SchemaDocument objects.
        """
        docs: list[SchemaDocument] = [
            self.build_table_document(
                table=table,
                schema_name=schema_name,
                database_id=database_id,
                schema_version=schema_version,
            )
        ]

        if include_columns:
            for col_name in table.list_column_names():
                col = table.get_column(col_name)
                if col is not None:
                    docs.append(
                        self.build_column_document(
                            table=table,
                            column=col,
                            schema_name=schema_name,
                            database_id=database_id,
                            schema_version=schema_version,
                        )
                    )

        return docs

    def build_documents_for_schema(
        self,
        schema: DatabaseSchemaEntity,
        include_columns: bool = True,
    ) -> list[SchemaDocument]:
        """
        Generate all schema documents across all tables in a DatabaseSchemaEntity.

        Args:
            schema: Target DatabaseSchemaEntity.
            include_columns: Whether to generate individual column documents.

        Returns:
            List of SchemaDocument objects representing the entire schema.
        """
        docs: list[SchemaDocument] = []
        for tbl_name in schema.list_table_names():
            table = schema.get_table(tbl_name)
            if table is not None:
                docs.extend(
                    self.build_documents_for_table(
                        table=table,
                        include_columns=include_columns,
                        schema_name=schema.schema_name,
                        database_id=schema.database_id,
                        schema_version=schema.version,
                    )
                )
        return docs
