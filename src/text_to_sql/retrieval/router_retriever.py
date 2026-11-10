"""
Router schema retriever orchestrating intent-based dynamic retrieval.

Routes questions dynamically to SchemaRetriever, EntityVectorStore, or both,
injecting exact WHERE filter value hints while enforcing strict Python RBAC.
"""
from typing import Sequence

from rbac.access_context import (
    ResolvedAccessContext,
)
from text_to_sql.retrieval.retriever_interface import ISchemaRetriever
from text_to_sql.schema.authorized_schema import (
    AuthorizedSchemaService,
)
from text_to_sql.retrieval.intent_classifier import (
    QueryIntentClassifier,
)
from text_to_sql.retrieval.retrieval import (
    HybridSchemaRetriever,
)
from text_to_sql.vector_store.entity_document import (
    EntityMatchResult,
    RetrievalIntent,
)
from text_to_sql.vector_store.entity_vector_store import (
    EntityVectorStore,
)


class RouterSchemaRetriever(ISchemaRetriever):
    """
    Unified router retriever dynamically executing schema and/or entity retrieval.
    """

    def __init__(
        self,
        schema_retriever: HybridSchemaRetriever,
        entity_store: EntityVectorStore,
        intent_classifier: QueryIntentClassifier | None = None,
        authorized_schema_service: AuthorizedSchemaService | None = None,
    ) -> None:
        """
        Initialize router retriever.

        Args:
            schema_retriever: HybridSchemaRetriever instance.
            entity_store: EntityVectorStore instance.
            intent_classifier: Optional QueryIntentClassifier.
            authorized_schema_service: Optional AuthorizedSchemaService.
        """
        self._schema_retriever = schema_retriever
        self._entity_store = entity_store
        self._classifier = intent_classifier or QueryIntentClassifier()
        self._schema_service = authorized_schema_service or AuthorizedSchemaService()

    async def retrieve_authorized_schema(
        self,
        query: str,
        access_context: ResolvedAccessContext,
        top_k_tables: int = 5,
    ) -> str:
        """
        Retrieve authorized schema and exact entity filter hints based on query intent.

        Args:
            query: User's natural language question.
            access_context: Resolved caller access context.
            top_k_tables: Maximum number of tables to project.

        Returns:
            Authorized prompt schema formatted with exact entity filter hints.
        """
        intent = self._classifier.classify_intent(query)

        # 1. SCHEMA_ONLY Intent: Skip entity search completely
        if intent == RetrievalIntent.SCHEMA_ONLY:
            return await self._schema_retriever.retrieve_authorized_schema(
                query=query,
                access_context=access_context,
                top_k_tables=top_k_tables,
            )

        # 2. Search entity values
        entity_matches: list[EntityMatchResult] = await self._entity_store.search_entities(
            query=query,
            access_context=access_context,
            top_k=3,
        )

        # 3. Candidate table collection
        candidate_tables: list[str] = []
        if entity_matches:
            # Boost matched entities' parent tables
            candidate_tables.extend(m.table_name for m in entity_matches)

        if intent == RetrievalIntent.HYBRID_BOTH or not candidate_tables:
            # Fetch structural schema candidates
            schema_candidates = await self._schema_retriever.retrieve_candidate_tables(
                query=query,
                top_k=top_k_tables,
            )
            for tbl in schema_candidates:
                if tbl not in candidate_tables:
                    candidate_tables.append(tbl)

        # 4. RBAC Gating on tables
        allowed_set = {t.lower() for t in access_context.allowed_tables}
        admitted_tables: list[str] = [
            t for t in candidate_tables if t.lower() in allowed_set
        ][:top_k_tables]

        if not admitted_tables and access_context.allowed_tables:
            admitted_tables = list(access_context.allowed_tables[:top_k_tables])

        # 5. Format prompt schema
        prompt_schema = self._schema_service.build_prompt_schema(
            access_context=access_context,
            target_tables=admitted_tables,
        )

        # 6. Append Exact Entity Filter Hints if matching entities were found
        admitted_set_lower = {t.lower() for t in admitted_tables}
        permitted_matches = [
            m for m in entity_matches if m.table_name.lower() in admitted_set_lower
        ]

        if permitted_matches:
            lines = [
                prompt_schema,
                "",
                "### Exact Entity Filter Hints",
                "The following verified database entity values matched the user query:",
            ]
            for m in permitted_matches:
                lines.append(
                    f"- `{m.table_name}.{m.primary_key_column} = '{m.primary_key_value}'` "
                    f"({m.entity_label})"
                )
            return "\n".join(lines)

        return prompt_schema
