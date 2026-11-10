"""
Abstract SQL execution port.

Defines the contract for executing read-only SQL queries and retrieving schema metadata
against the analytical database (Text-to-SQL execution engine).
"""
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class ColumnSchema(BaseModel):
    """Metadata for a single table column."""

    model_config = ConfigDict(frozen=True)

    name: str
    data_type: str
    is_nullable: bool = True
    description: str | None = None


class TableSchema(BaseModel):
    """Metadata description for a database table."""

    model_config = ConfigDict(frozen=True)

    table_name: str
    schema_name: str = "public"
    columns: list[ColumnSchema] = Field(default_factory=list)
    description: str | None = None


class SqlExecutionResult(BaseModel):
    """Structured result set returned from analytical SQL execution."""

    model_config = ConfigDict(frozen=True)

    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: float
    truncated: bool = False


class SqlExecutorProtocol(Protocol):
    """Protocol for executing validated SQL queries and retrieving database schemas."""

    async def execute_query(
        self,
        sql: str,
        parameters: dict[str, Any] | None = None,
        timeout_ms: int = 5000,
        max_rows: int = 1000,
    ) -> SqlExecutionResult:
        """Execute a read-only query safely with timeout and row limit guards."""
        ...

    async def get_table_schema(self, table_name: str, schema: str = "public") -> TableSchema:
        """Retrieve column types and metadata for a specific table."""
        ...

    async def list_tables(self, schema: str = "public") -> list[str]:
        """List all accessible tables in the schema."""
        ...
