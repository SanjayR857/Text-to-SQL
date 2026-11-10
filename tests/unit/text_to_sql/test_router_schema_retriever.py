"""
Unit tests for RouterSchemaRetriever.

Verifies:
    1. SCHEMA_ONLY intent executes only schema retrieval (skips entity store).
    2. HYBRID_BOTH intent executes both and appends Exact Entity Filter Hints.
    3. RBAC isolation: Entities from unauthorized tables are dropped from hints.
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

from auth import PolicyResolver
from text_to_sql import (
    AuthorizedSchemaService,
    HybridSchemaRetriever,
    QueryIntentClassifier,
    RouterSchemaRetriever,
)
from auth.user import (
    AccessScope as UserAccessScope,
    UserContext,
)
from text_to_sql import (
    EntityMatchResult,
    RetrievalIntent,
)
from text_to_sql.entity_vector_store import (
    EntityVectorStore,
)


@pytest.fixture
def unassigned_employee_user() -> UserContext:
    """Fixture for regular employee."""
    return UserContext(
        user_id=uuid4(),
        email="dev@company.com",
        assignments=[],
        access_scope=UserAccessScope(vertical_codes=[], project_ids=[]),
    )


class TestRouterSchemaRetriever:
    """Tests for RouterSchemaRetriever dynamic execution and hint generation."""

    @pytest.mark.asyncio
    async def test_schema_only_intent_skips_entity_store(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """When query is classified as SCHEMA_ONLY, entity_store is never queried."""
        mock_schema_retriever = MagicMock(spec=HybridSchemaRetriever)
        mock_schema_retriever.retrieve_authorized_schema = AsyncMock(
            return_value="### Authorized Database Schema\n#### Table: `EmployeeInformation`"
        )

        mock_entity_store = MagicMock(spec=EntityVectorStore)
        mock_entity_store.search_entities = AsyncMock()

        mock_classifier = MagicMock(spec=QueryIntentClassifier)
        mock_classifier.classify_intent = MagicMock(return_value=RetrievalIntent.SCHEMA_ONLY)

        resolver = PolicyResolver()
        access_context = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["EmployeeInformation"],
        )

        router = RouterSchemaRetriever(
            schema_retriever=mock_schema_retriever,
            entity_store=mock_entity_store,
            intent_classifier=mock_classifier,
        )

        result = await router.retrieve_authorized_schema(
            query="How many total employees are active?",
            access_context=access_context,
        )

        assert "EmployeeInformation" in result
        mock_schema_retriever.retrieve_authorized_schema.assert_awaited_once()
        mock_entity_store.search_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_hybrid_both_injects_entity_filter_hints(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """HYBRID_BOTH intent queries entities and appends exact filter hints."""
        mock_schema_retriever = MagicMock(spec=HybridSchemaRetriever)
        mock_schema_retriever.retrieve_candidate_tables = AsyncMock(
            return_value=["EmployeeInformation"]
        )

        mock_entity_store = MagicMock(spec=EntityVectorStore)
        mock_entity_store.search_entities = AsyncMock(
            return_value=[
                EntityMatchResult(
                    table_name="EmployeeInformation",
                    primary_key_column="employeeMailId",
                    primary_key_value="john.doe@company.com",
                    entity_label="John Doe <john.doe@company.com>",
                    score=0.92,
                    matched_text="John Doe employee",
                )
            ]
        )

        mock_classifier = MagicMock(spec=QueryIntentClassifier)
        mock_classifier.classify_intent = MagicMock(return_value=RetrievalIntent.HYBRID_BOTH)

        resolver = PolicyResolver()
        access_context = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["EmployeeInformation"],
        )

        router = RouterSchemaRetriever(
            schema_retriever=mock_schema_retriever,
            entity_store=mock_entity_store,
            intent_classifier=mock_classifier,
            authorized_schema_service=AuthorizedSchemaService(),
        )

        result = await router.retrieve_authorized_schema(
            query="Show John Doe's profile",
            access_context=access_context,
        )

        # Prompt schema and entity filter hints present
        assert "EmployeeInformation" in result
        assert "### Exact Entity Filter Hints" in result
        assert "EmployeeInformation.employeeMailId = 'john.doe@company.com'" in result

    @pytest.mark.asyncio
    async def test_rbac_drops_unauthorized_entity_matches(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Entities matching unauthorized tables (e.g. Scoreboard) are omitted from hints."""
        mock_schema_retriever = MagicMock(spec=HybridSchemaRetriever)
        mock_schema_retriever.retrieve_candidate_tables = AsyncMock(
            return_value=["EmployeeInformation"]
        )

        mock_entity_store = MagicMock(spec=EntityVectorStore)
        mock_entity_store.search_entities = AsyncMock(
            return_value=[
                EntityMatchResult(
                    table_name="Scoreboard",  # Forbidden for regular employee
                    primary_key_column="id",
                    primary_key_value="SC-001",
                    entity_label="Top Performer (SC-001)",
                    score=0.94,
                    matched_text="Scoreboard row",
                )
            ]
        )

        mock_classifier = MagicMock(spec=QueryIntentClassifier)
        mock_classifier.classify_intent = MagicMock(return_value=RetrievalIntent.HYBRID_BOTH)

        resolver = PolicyResolver()
        # Resolve permissions - Scoreboard is not permitted
        access_context = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["EmployeeInformation"],
        )

        router = RouterSchemaRetriever(
            schema_retriever=mock_schema_retriever,
            entity_store=mock_entity_store,
            intent_classifier=mock_classifier,
            authorized_schema_service=AuthorizedSchemaService(),
        )

        result = await router.retrieve_authorized_schema(
            query="Show top performer scoreboard",
            access_context=access_context,
        )

        # Scoreboard dropped completely from both schema and entity hints
        assert "Scoreboard" not in result
        assert "SC-001" not in result
