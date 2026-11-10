"""
Table and column metadata domain entities.

Represents canonical table definitions, column types, keys, relationships,
and business descriptions for structured data sources.
"""
from pydantic import BaseModel, ConfigDict, Field


class ForeignKeyRelation(BaseModel):
    """
    Foreign key relationship definition between tables.
    """

    model_config = ConfigDict(frozen=True)

    constrained_columns: list[str] = Field(
        ...,
        description="Local column names forming the foreign key",
    )
    referred_schema: str = Field(
        default="public",
        description="Target schema name",
    )
    referred_table: str = Field(
        ...,
        description="Target table name",
    )
    referred_columns: list[str] = Field(
        ...,
        description="Target column names referenced in the target table",
    )


class ColumnMetadataEntity(BaseModel):
    """
    Metadata representation of an individual table column.

    Combines physical schema attributes (type, nullability, keys) with
    business-level documentation (description, synonyms, samples, sensitivity).
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(
        ...,
        description="Canonical column name as defined in database",
    )
    data_type: str = Field(
        ...,
        description="SQL data type (e.g., VARCHAR, INTEGER, TIMESTAMP, NUMERIC)",
    )
    is_nullable: bool = Field(
        default=True,
        description="Whether column permits NULL values",
    )
    is_primary_key: bool = Field(
        default=False,
        description="Whether column is part of primary key",
    )
    is_foreign_key: bool = Field(
        default=False,
        description="Whether column references another table",
    )
    foreign_key_target: str | None = Field(
        default=None,
        description="Referenced target column in 'TargetTable.column' format",
    )
    description: str | None = Field(
        default=None,
        description="Curated business description explaining column semantics",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Business synonyms and common terms mapped to this column",
    )
    sample_values: list[str] = Field(
        default_factory=list,
        description="Representative sample or distinct values for LLM disambiguation",
    )
    sensitivity: str | None = Field(
        default=None,
        description="Data sensitivity classification (e.g., PUBLIC, INTERNAL, RESTRICTED, CONFIDENTIAL)",
    )


class TableMetadataEntity(BaseModel):
    """
    Metadata representation of a database table.

    Aggregates column metadata, primary key constraints, foreign key
    relationships, indexes, and curated business documentation.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(
        ...,
        description="Canonical table name",
    )
    schema_name: str = Field(
        default="public",
        description="Database schema name",
    )
    database_id: str = Field(
        default="default",
        description="Logical database identifier",
    )
    description: str | None = Field(
        default=None,
        description="Curated business description explaining the purpose of this table",
    )
    synonyms: list[str] = Field(
        default_factory=list,
        description="Business synonyms and domain aliases for the table",
    )
    columns: dict[str, ColumnMetadataEntity] = Field(
        default_factory=dict,
        description="Column definitions keyed by lowercase column name for fast lookup",
    )
    primary_keys: list[str] = Field(
        default_factory=list,
        description="Primary key column names in original casing",
    )
    foreign_keys: list[ForeignKeyRelation] = Field(
        default_factory=list,
        description="Foreign key relationships originating from this table",
    )
    indexes: list[str] = Field(
        default_factory=list,
        description="Index names defined on this table",
    )
    row_count_estimate: int | None = Field(
        default=None,
        description="Estimated row count for query planning and complexity evaluation",
    )

    def get_column(self, column_name: str) -> ColumnMetadataEntity | None:
        """
        Retrieve column metadata case-insensitively.

        Args:
            column_name: Name of column to retrieve.

        Returns:
            ColumnMetadataEntity if found, None otherwise.
        """
        if not column_name:
            return None
        return self.columns.get(column_name.strip().lower())

    def has_column(self, column_name: str) -> bool:
        """
        Check whether a column exists case-insensitively.

        Args:
            column_name: Name of column to check.
        """
        if not column_name:
            return False
        return column_name.strip().lower() in self.columns

    def list_column_names(self) -> list[str]:
        """
        List all column names preserving their original casing.
        """
        return [col.name for col in self.columns.values()]
