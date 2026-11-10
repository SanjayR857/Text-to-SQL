"""
Schema change domain events and mutation types.

Defines the event contracts published when database DDL migrations, table alterations,
or catalog metadata updates occur across registered data sources.
"""
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SchemaChangeType(str, Enum):
    """
    Nature of the schema modification event.
    """

    CREATED = "CREATED"
    ALTERED = "ALTERED"
    DROPPED = "DROPPED"
    REFRESH_ALL = "REFRESH_ALL"


class SchemaChangeEvent(BaseModel):
    """
    Immutable domain event emitted upon physical or metadata schema changes.
    """

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the schema change event",
    )
    database_id: str = Field(
        default="default",
        description="Logical database identifier where schema changed",
    )
    schema_name: str = Field(
        default="public",
        description="PostgreSQL schema name (e.g. 'public')",
    )
    change_type: SchemaChangeType = Field(
        ...,
        description="Type of schema mutation (CREATED, ALTERED, DROPPED, REFRESH_ALL)",
    )
    affected_tables: list[str] = Field(
        default_factory=list,
        description="Names of tables affected by the mutation (empty for REFRESH_ALL)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the schema change occurred",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Optional tracing correlation ID / request ID",
    )
