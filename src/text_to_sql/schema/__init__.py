"""
Database schema introspection, domain metadata entities, catalog, and RBAC projections.
"""
from text_to_sql.schema.catalog import (
    ColumnBusinessMetadata,
    EnterpriseMetadataCatalog,
    TableBusinessMetadata,
)
from text_to_sql.schema.introspector import PostgresSchemaIntrospector
from text_to_sql.schema.metadata import (
    ColumnMetadataEntity,
    ForeignKeyRelation,
    TableMetadataEntity,
)
from text_to_sql.schema.database_schema import DatabaseSchemaEntity
from text_to_sql.schema.authorized_schema import AuthorizedSchemaService
from text_to_sql.schema.schema_events import (
    SchemaChangeEvent,
    SchemaChangeType,
)

__all__ = [
    "EnterpriseMetadataCatalog",
    "TableBusinessMetadata",
    "ColumnBusinessMetadata",
    "PostgresSchemaIntrospector",
    "TableMetadataEntity",
    "ColumnMetadataEntity",
    "ForeignKeyRelation",
    "DatabaseSchemaEntity",
    "AuthorizedSchemaService",
    "SchemaChangeEvent",
    "SchemaChangeType",
]
