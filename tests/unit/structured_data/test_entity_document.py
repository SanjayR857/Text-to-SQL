"""
Unit tests for EntityValueDocument and EntityTableConfig domain models.

Verifies:
    1. EntityTableConfig defaults and registry.
    2. EntityValueDocument deterministic ID and SHA-256 hash generation.
    3. Immutability across entity domain models.
"""
import pytest
from pydantic import ValidationError

from enterprise_ai_platform.domain.structured_data import (
    DEFAULT_ENTITY_TABLE_CONFIGS,
    EntityTableConfig,
    EntityValueDocument,
    RetrievalIntent,
)


class TestEntityDocument:
    """Tests for EntityValueDocument and EntityTableConfig."""

    def test_default_entity_configs_registered(self) -> None:
        """Pre-configured entity table configurations exist for ProjectName, Vertical, EmployeeInformation."""
        assert "projectname" in DEFAULT_ENTITY_TABLE_CONFIGS
        assert "vertical" in DEFAULT_ENTITY_TABLE_CONFIGS
        assert "employeeinformation" in DEFAULT_ENTITY_TABLE_CONFIGS

        proj_cfg = DEFAULT_ENTITY_TABLE_CONFIGS["projectname"]
        assert proj_cfg.primary_key_column == "id"
        assert "projectName" in proj_cfg.searchable_columns
        assert proj_cfg.vertical_code_column == "verticalCode"

    def test_build_document_id_deterministic(self) -> None:
        """Entity document ID generates deterministic string."""
        doc_id = EntityValueDocument.build_document_id(
            database_id="MainDb",
            schema_name="Public",
            table_name="ProjectName",
            primary_key_value="PRJ-001",
        )
        assert doc_id == "maindb:public:projectname:prj-001:ENTITY"

    def test_create_entity_value_document(self) -> None:
        """Factory creates valid, immutable EntityValueDocument."""
        doc = EntityValueDocument.create(
            table_name="ProjectName",
            primary_key_column="id",
            primary_key_value="PRJ-001",
            entity_label="Apollo AI Migration (ID: PRJ-001)",
            searchable_text="Project: Apollo AI Migration (ID: PRJ-001), Vertical: CHAIO",
            vertical_code="CHAIO",
            project_id="PRJ-001",
        )

        assert doc.document_id == "default:public:projectname:prj-001:ENTITY"
        assert doc.table_name == "ProjectName"
        assert doc.primary_key_value == "PRJ-001"
        assert doc.metadata["vertical_code"] == "CHAIO"
        assert doc.metadata["project_id"] == "PRJ-001"
        assert len(doc.content_hash) == 64

        # Immutability
        with pytest.raises(ValidationError):
            doc.table_name = "Other"  # type: ignore[misc]

    def test_retrieval_intent_values(self) -> None:
        """RetrievalIntent enum has expected keys."""
        assert RetrievalIntent.SCHEMA_ONLY.value == "SCHEMA_ONLY"
        assert RetrievalIntent.ENTITY_ONLY.value == "ENTITY_ONLY"
        assert RetrievalIntent.HYBRID_BOTH.value == "HYBRID_BOTH"
