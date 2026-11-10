"""
Application interface ports package.

Contains abstract protocols and data models decoupling the core business logic
from infrastructure tools (LLMs, embeddings, vector databases, object storage,
SQL execution, and LangGraph checkpointers).
"""
from enterprise_ai_platform.application.interfaces.checkpoint_store import (
    CheckpointRecord,
    CheckpointStoreProtocol,
)
from enterprise_ai_platform.application.interfaces.document_parser import (
    DocumentParserProtocol,
    ParsedDocument,
    ParsedTable,
)
from enterprise_ai_platform.application.interfaces.document_storage import (
    DocumentStorageProtocol,
)
from enterprise_ai_platform.application.interfaces.embedding_provider import (
    EmbeddingProviderProtocol,
)
from enterprise_ai_platform.application.interfaces.llm_provider import (
    ChatMessage,
    LLMCompletionResponse,
    LLMProviderProtocol,
)
from enterprise_ai_platform.application.interfaces.retriever import (
    RetrieverProtocol,
)
from enterprise_ai_platform.application.interfaces.sql_executor import (
    ColumnSchema,
    SqlExecutionResult,
    SqlExecutorProtocol,
    TableSchema,
)
from enterprise_ai_platform.application.interfaces.vector_store import (
    VectorDocument,
    VectorSearchResult,
    VectorStoreProtocol,
)

__all__ = [
    # LLM & Embeddings
    "ChatMessage",
    "LLMCompletionResponse",
    "LLMProviderProtocol",
    "EmbeddingProviderProtocol",
    # Vector Search & Retrieval
    "VectorDocument",
    "VectorSearchResult",
    "VectorStoreProtocol",
    "RetrieverProtocol",
    # Document Processing & Storage
    "ParsedDocument",
    "ParsedTable",
    "DocumentParserProtocol",
    "DocumentStorageProtocol",
    # Structured Data & SQL Execution
    "ColumnSchema",
    "TableSchema",
    "SqlExecutionResult",
    "SqlExecutorProtocol",
    # Checkpointing
    "CheckpointRecord",
    "CheckpointStoreProtocol",
]
