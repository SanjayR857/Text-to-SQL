"""
Domain models for structured data, database schemas, and schema embedding documents.
"""
from enterprise_ai_platform.domain.structured_data.database_schema import (
    DatabaseSchemaEntity,
)
from enterprise_ai_platform.domain.structured_data.entity_document import (
    DEFAULT_ENTITY_TABLE_CONFIGS,
    EntityMatchResult,
    EntityTableConfig,
    EntityValueDocument,
    RetrievalIntent,
)
from enterprise_ai_platform.domain.structured_data.schema_document import (
    SchemaDocument,
    SchemaDocumentType,
)
from enterprise_ai_platform.domain.structured_data.schema_events import (
    SchemaChangeEvent,
    SchemaChangeType,
)
from enterprise_ai_platform.domain.structured_data.table_metadata import (
    ColumnMetadataEntity,
    ForeignKeyRelation,
    TableMetadataEntity,
)

__all__ = [
    "ColumnMetadataEntity",
    "DatabaseSchemaEntity",
    "DEFAULT_ENTITY_TABLE_CONFIGS",
    "EntityMatchResult",
    "EntityTableConfig",
    "EntityValueDocument",
    "ForeignKeyRelation",
    "RetrievalIntent",
    "SchemaChangeEvent",
    "SchemaChangeType",
    "SchemaDocument",
    "SchemaDocumentType",
    "TableMetadataEntity",
]
