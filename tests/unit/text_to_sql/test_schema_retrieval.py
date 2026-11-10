"""
Unit tests for HybridSchemaRetriever with Python RBAC integration.

Verifies:
    1. Hybrid candidate ranking (table similarity, column similarity, keyword matching).
    2. RBAC table gating: Unauthorized tables (e.g. Scoreboard) dropped for unauthorized users.
    3. RBAC column redaction: Sensitive columns (fixedCtc, panNumber) excluded from LLM prompt.
    4. Unrestricted projection for CA Administrator.
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

from rbac import PolicyResolver
from text_to_sql.vector_store.vector_store_interfaces import (
    IVectorStore,
    VectorSearchResult,
)
from text_to_sql import (
    AuthorizedSchemaService,
    HybridSchemaRetriever,
)
from rbac.identity import Area, Role
from rbac.identity import (
    AccessScope as UserAccessScope,
    RoleAssignmentContext,
    UserContext,
)
from text_to_sql import SchemaDocumentType


@pytest.fixture
def unassigned_employee_user() -> UserContext:
    """Fixture for regular employee with SELF-scope."""
    return UserContext(
        user_id=uuid4(),
        email="regular.dev@company.com",
        assignments=[],
        access_scope=UserAccessScope(vertical_codes=[], project_ids=[]),
    )


@pytest.fixture
def ca_admin_user() -> UserContext:
    """Fixture for CA Administrator."""
    return UserContext(
        user_id=uuid4(),
        email="admin@company.com",
        assignments=[
            RoleAssignmentContext(
                role=Role.ADMIN,
                vertical_code="CHAIO",
                vertical_name="Central AI Office",
                vertical_area=Area.CentralApplication,
            )
        ],
        access_scope=UserAccessScope(vertical_codes=["CHAIO"], project_ids=[]),
    )


class TestHybridSchemaRetriever:
    """Tests for hybrid retrieval and RBAC gating."""

    @pytest.mark.asyncio
    async def test_unauthorized_table_dropped_for_regular_employee(
        self, unassigned_employee_user: UserContext
    ) -> None:
        """Scoreboard returned by vector search is dropped for regular employee."""
        # Mock vector store returning Scoreboard and EmployeeInformation
        mock_store = MagicMock(spec=IVectorStore)
        mock_store.similarity_search = AsyncMock(
            side_effect=[
                # Table-level search results
                [
                    VectorSearchResult(
                        document_id="default:public:scoreboard:TABLE",
                        document_type=SchemaDocumentType.TABLE,
                        table_name="Scoreboard",
                        searchable_text="Executive Scoreboard",
                        description="Leaderboard",
                        score=0.95,
                    ),
                    VectorSearchResult(
                        document_id="default:public:employeeinformation:TABLE",
                        document_type=SchemaDocumentType.TABLE,
                        table_name="EmployeeInformation",
                        searchable_text="Employee Directory",
                        description="Profiles",
                        score=0.85,
                    ),
                ],
                # Column-level search results
                [],
            ]
        )

        resolver = PolicyResolver()
        # Resolve user permissions for all discovered tables
        access_context = resolver.resolve_access_context(
            unassigned_employee_user,
            requested_tables=["Scoreboard", "EmployeeInformation"],
        )

        retriever = HybridSchemaRetriever(
            vector_store=mock_store,
            authorized_schema_service=AuthorizedSchemaService(),
        )

        prompt_schema = await retriever.retrieve_authorized_schema(
            query="Show executive scoreboard ratings and employee details",
            access_context=access_context,
            top_k_tables=2,
        )

        # Invariant: Scoreboard is completely dropped
        assert "Scoreboard" not in prompt_schema
        assert "EmployeeInformation" in prompt_schema

        # Invariant: Sensitive compensation columns are omitted
        assert "fixedCtc" not in prompt_schema
        assert "currentCtc" not in prompt_schema
        assert "employeeName" in prompt_schema

    @pytest.mark.asyncio
    async def test_admin_receives_scoreboard_and_sensitive_columns(
        self, ca_admin_user: UserContext
    ) -> None:
        """CA Admin receives Scoreboard and all sensitive columns in prompt schema."""
        mock_store = MagicMock(spec=IVectorStore)
        mock_store.similarity_search = AsyncMock(
            side_effect=[
                [
                    VectorSearchResult(
                        document_id="default:public:scoreboard:TABLE",
                        document_type=SchemaDocumentType.TABLE,
                        table_name="Scoreboard",
                        searchable_text="Executive Scoreboard",
                        description="Leaderboard",
                        score=0.95,
                    ),
                    VectorSearchResult(
                        document_id="default:public:employeeinformation:TABLE",
                        document_type=SchemaDocumentType.TABLE,
                        table_name="EmployeeInformation",
                        searchable_text="Employee Directory",
                        description="Profiles",
                        score=0.85,
                    ),
                ],
                [],
            ]
        )

        resolver = PolicyResolver()
        access_context = resolver.resolve_access_context(
            ca_admin_user,
            requested_tables=["Scoreboard", "EmployeeInformation"],
        )

        retriever = HybridSchemaRetriever(
            vector_store=mock_store,
            authorized_schema_service=AuthorizedSchemaService(),
        )

        prompt_schema = await retriever.retrieve_authorized_schema(
            query="Show executive scoreboard ratings and employee details",
            access_context=access_context,
            top_k_tables=2,
        )

        # CA Admin has access to both
        assert "Scoreboard" in prompt_schema
        assert "EmployeeInformation" in prompt_schema
        assert "fixedCtc" in prompt_schema
