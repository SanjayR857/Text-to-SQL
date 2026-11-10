"""
Hybrid schema retriever service with Python RBAC authorization gating.

Combines LlamaIndex pgvector semantic search with exact token matching,
and enforces Python table and column RBAC before projecting schema into LLM prompts.
"""
from typing import Sequence

from rbac.access_context import (
    ResolvedAccessContext,
)
from text_to_sql.retrieval.retriever_interface import ISchemaRetriever
from text_to_sql.vector_store.vector_store_interfaces import (
    IVectorStore,
    VectorSearchResult,
)
from text_to_sql.schema.authorized_schema import (
    AuthorizedSchemaService,
)
from text_to_sql.schema.catalog import (
    EnterpriseMetadataCatalog,
)
from text_to_sql.vector_store.schema_document import (
    SchemaDocumentType,
)


class HybridSchemaRetriever(ISchemaRetriever):
    """
    Hybrid schema retriever orchestrating semantic vector search and RBAC authorization.

    Retrieval Workflow:
        1. Semantic search over table-level and column-level schema embeddings.
        2. Keyword/token matching across permitted table names.
        3. Strict RBAC gating: drops unauthorized tables and redacts confidential columns.
        4. Projects authorized schema and approved join hints for LLM prompt generation.
    """

    def __init__(
        self,
        vector_store: IVectorStore,
        authorized_schema_service: AuthorizedSchemaService | None = None,
        metadata_catalog: EnterpriseMetadataCatalog | None = None,
    ) -> None:
        """
        Initialize retriever.

        Args:
            vector_store: IVectorStore implementation (e.g., SchemaVectorStore).
            authorized_schema_service: Service projecting authorized schema and join hints.
            metadata_catalog: Enterprise business metadata catalog.
        """
        self._vector_store = vector_store
        self._schema_service = authorized_schema_service or AuthorizedSchemaService()
        self._catalog = metadata_catalog or EnterpriseMetadataCatalog()

    async def retrieve_candidate_tables(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[str]:
        """
        Retrieve candidate table names via vector search and keyword matching.

        Args:
            query: User's natural language question.
            top_k: Maximum candidate tables to return.

        Returns:
            Ranked list of candidate table names.
        """
        table_scores: dict[str, float] = {}

        # 1. Semantic search on TABLE documents
        table_results = await self._vector_store.similarity_search(
            query=query,
            top_k=top_k,
            document_type=SchemaDocumentType.TABLE,
        )
        for r in table_results:
            table_scores[r.table_name] = max(table_scores.get(r.table_name, 0.0), r.score)

        # 2. Semantic search on COLUMN documents (weights parent table)
        col_results = await self._vector_store.similarity_search(
            query=query,
            top_k=top_k * 2,
            document_type=SchemaDocumentType.COLUMN,
        )
        for r in col_results:
            # Add column score with slight discount (0.9x) to favor direct table matches
            col_score = r.score * 0.9
            table_scores[r.table_name] = max(table_scores.get(r.table_name, 0.0), col_score)

        # 3. Exact keyword matching in query text
        query_lower = query.lower()
        for tbl_name in table_scores.keys():
            if tbl_name.lower() in query_lower:
                table_scores[tbl_name] = table_scores[tbl_name] + 0.5

        # Sort by composite relevance score descending
        sorted_tables = sorted(
            table_scores.keys(),
            key=lambda t: table_scores[t],
            reverse=True,
        )
        return sorted_tables[:top_k]

    async def retrieve_authorized_schema(
        self,
        query: str,
        access_context: ResolvedAccessContext,
        top_k_tables: int = 5,
    ) -> str:
        """
        Retrieve, filter, and format authorized schema context for a natural language query.

        Args:
            query: Natural language user question.
            access_context: Resolved caller access context from PolicyResolver.
            top_k_tables: Maximum number of tables to project.

        Returns:
            Authorized schema markdown string ready for LLM prompt ingestion.
        """
        # 1. Retrieve candidates
        candidates = await self.retrieve_candidate_tables(query=query, top_k=top_k_tables * 2)

        # 2. Gate candidates against caller's permitted tables
        allowed_set = {t.lower() for t in access_context.allowed_tables}
        admitted_tables: list[str] = []

        for candidate in candidates:
            if candidate.lower() in allowed_set:
                perm = access_context.get_table_permission(candidate)
                if perm and perm.can_read:
                    admitted_tables.append(perm.table_name)

            if len(admitted_tables) >= top_k_tables:
                break

        # Fallback if no vector search candidates matched permitted tables
        if not admitted_tables and access_context.allowed_tables:
            admitted_tables = list(access_context.allowed_tables[:top_k_tables])

        # 3. Project authorized schema and approved join hints
        return self._schema_service.build_prompt_schema(
            access_context=access_context,
            target_tables=admitted_tables,
        )
