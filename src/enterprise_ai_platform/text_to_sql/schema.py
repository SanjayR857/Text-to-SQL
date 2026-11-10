"""
DatabaseSchema entity representing the full schema of a registered structured data source.

Maintains an immutable inventory of table definitions, version tracking,
and lookup methods across the database schema.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from enterprise_ai_platform.text_to_sql.metadata import (
    ColumnMetadataEntity,
    TableMetadataEntity,
)


class DatabaseSchemaEntity(BaseModel):
    """
    Canonical representation of an entire database schema.

    Encapsulates all tables, their column definitions, relationships,
    introspection timestamp, and version metadata.
    """

    model_config = ConfigDict(frozen=True)

    database_id: str = Field(
        default="default",
        description="Logical database identifier",
    )
    schema_name: str = Field(
        default="public",
        description="PostgreSQL schema name",
    )
    version: str = Field(
        default="1.0.0",
        description="Schema or catalog version identifier",
    )
    tables: dict[str, TableMetadataEntity] = Field(
        default_factory=dict,
        description="Tables keyed by lowercase table name for case-insensitive lookup",
    )
    last_introspected_at: datetime | None = Field(
        default=None,
        description="Timestamp of the most recent database introspection",
    )
    description: str | None = Field(
        default=None,
        description="High-level description of the database domain or schema",
    )

    def get_table(self, table_name: str) -> TableMetadataEntity | None:
        """
        Retrieve table metadata case-insensitively.

        Args:
            table_name: Table name to look up.

        Returns:
            TableMetadataEntity if found, None otherwise.
        """
        if not table_name:
            return None
        return self.tables.get(table_name.strip().lower())

    def has_table(self, table_name: str) -> bool:
        """
        Check whether a table exists case-insensitively.

        Args:
            table_name: Table name to check.
        """
        if not table_name:
            return False
        return table_name.strip().lower() in self.tables

    def get_column(
        self,
        table_name: str,
        column_name: str,
    ) -> ColumnMetadataEntity | None:
        """
        Retrieve column metadata across tables case-insensitively.

        Args:
            table_name: Target table name.
            column_name: Target column name.

        Returns:
            ColumnMetadataEntity if found, None otherwise.
        """
        table = self.get_table(table_name)
        if not table:
            return None
        return table.get_column(column_name)

    def list_table_names(self) -> list[str]:
        """
        List all canonical table names preserving original casing.
        """
        return [tbl.name for tbl in self.tables.values()]

    @property
    def total_tables_count(self) -> int:
        """
        Total number of tables registered in the schema.
        """
        return len(self.tables)

    @property
    def total_columns_count(self) -> int:
        """
        Total number of columns registered across all tables in the schema.
        """
        return sum(len(tbl.columns) for tbl in self.tables.values())
