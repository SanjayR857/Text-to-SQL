"""
Text-to-SQL engine: database schema introspection, metadata catalog, pgvector stores,
query intent classification, scope resolution, and AST validation.
"""
from enterprise_ai_platform.text_to_sql.ast_validator import (
    ALLOWED_FUNCTIONS,
    PROHIBITED_FUNCTIONS,
    SqlAstValidator,
)
from enterprise_ai_platform.text_to_sql.authorized_schema import (
    AuthorizedSchemaService,
)
from enterprise_ai_platform.text_to_sql.catalog import (
    ColumnBusinessMetadata,
    EnterpriseMetadataCatalog,
    TableBusinessMetadata,
)
from enterprise_ai_platform.text_to_sql.document_builder import SchemaDocumentBuilder
from enterprise_ai_platform.text_to_sql.embedding_worker import SchemaEmbeddingWorker
from enterprise_ai_platform.text_to_sql.entity_document import (
    DEFAULT_ENTITY_TABLE_CONFIGS,
    EntityMatchResult,
    EntityTableConfig,
    EntityValueDocument,
    RetrievalIntent,
)
from enterprise_ai_platform.text_to_sql.entity_vector_store import (
    EntityLlamaIndexRetriever,
    EntityVectorStore,
)
from enterprise_ai_platform.text_to_sql.entity_worker import EntityEmbeddingWorker
from enterprise_ai_platform.text_to_sql.intent_classifier import (
    QueryIntentClassifier,
)
from enterprise_ai_platform.text_to_sql.introspector import PostgresSchemaIntrospector
from enterprise_ai_platform.text_to_sql.metadata import (
    ColumnMetadataEntity,
    ForeignKeyRelation,
    TableMetadataEntity,
)
from enterprise_ai_platform.text_to_sql.models import (
    EntityEmbeddingModel,
    SchemaEmbeddingModel,
)
from enterprise_ai_platform.text_to_sql.policy_enforcer import SqlPolicyEnforcer
from enterprise_ai_platform.text_to_sql.predicate_injector import RowPredicateInjector
from enterprise_ai_platform.text_to_sql.retrieval import (
    HybridSchemaRetriever,
)
from enterprise_ai_platform.text_to_sql.retriever_interface import ISchemaRetriever
from enterprise_ai_platform.text_to_sql.router_retriever import RouterSchemaRetriever
from enterprise_ai_platform.text_to_sql.schema import (
    DatabaseSchemaEntity,
)
from enterprise_ai_platform.text_to_sql.schema_document import (
    SchemaDocument,
    SchemaDocumentType,
)
from enterprise_ai_platform.text_to_sql.schema_events import (
    SchemaChangeEvent,
    SchemaChangeType,
)
from enterprise_ai_platform.text_to_sql.schema_vector_store import (
    SchemaLlamaIndexRetriever,
    SchemaVectorStore,
)
from enterprise_ai_platform.text_to_sql.scope_resolver import SqlScopeResolver
from enterprise_ai_platform.text_to_sql.vector_store_interfaces import (
    IVectorStore,
    VectorSearchResult,
)

__all__ = [
    "ALLOWED_FUNCTIONS",
    "AuthorizedSchemaService",
    "ColumnBusinessMetadata",
    "ColumnMetadataEntity",
    "DatabaseSchemaEntity",
    "DEFAULT_ENTITY_TABLE_CONFIGS",
    "EnterpriseMetadataCatalog",
    "EntityEmbeddingModel",
    "EntityEmbeddingWorker",
    "EntityLlamaIndexRetriever",
    "EntityMatchResult",
    "EntityTableConfig",
    "EntityValueDocument",
    "EntityVectorStore",
    "ForeignKeyRelation",
    "HybridSchemaRetriever",
    "ISchemaRetriever",
    "IVectorStore",
    "PROHIBITED_FUNCTIONS",
    "PostgresSchemaIntrospector",
    "QueryIntentClassifier",
    "RetrievalIntent",
    "RouterSchemaRetriever",
    "RowPredicateInjector",
    "SchemaChangeEvent",
    "SchemaChangeType",
    "SchemaDocument",
    "SchemaDocumentBuilder",
    "SchemaDocumentType",
    "SchemaEmbeddingModel",
    "SchemaEmbeddingWorker",
    "SchemaLlamaIndexRetriever",
    "SchemaVectorStore",
    "SqlAstValidator",
    "SqlPolicyEnforcer",
    "SqlScopeResolver",
    "TableBusinessMetadata",
    "TableMetadataEntity",
    "VectorSearchResult",
]
