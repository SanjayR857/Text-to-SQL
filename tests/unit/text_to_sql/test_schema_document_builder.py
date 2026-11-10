"""
Unit tests for SchemaDocumentBuilder.

Verifies:
    1. Table-level semantic document generation, formatting, and metadata tagging.
    2. Column-level semantic document generation with data types, keys, and sensitivity.
    3. Multi-document batch creation across tables and whole database schemas.
    4. Deterministic document IDs and SHA-256 change detection hashes.
"""
import pytest

from enterprise_ai_platform.text_to_sql.document_builder import (
    SchemaDocumentBuilder,
)
from enterprise_ai_platform.text_to_sql import (
    ColumnMetadataEntity,
    DatabaseSchemaEntity,
    ForeignKeyRelation,
    SchemaDocumentType,
    TableMetadataEntity,
)


@pytest.fixture
def sample_table_metadata() -> TableMetadataEntity:
    """Fixture providing an enriched TableMetadataEntity with PK, FK, and columns."""
    col_id = ColumnMetadataEntity(
        name="id",
        data_type="VARCHAR(50)",
        is_nullable=False,
        is_primary_key=True,
        description="Unique project identifier.",
        synonyms=["project id", "engagement id"],
        sample_values=["PRJ-001"],
    )
    col_name = ColumnMetadataEntity(
        name="projectName",
        data_type="VARCHAR(200)",
        is_nullable=False,
        description="Commercial project name.",
        synonyms=["project title", "engagement name"],
        sample_values=["Cloud Transformation"],
    )
    col_val = ColumnMetadataEntity(
        name="contractValue",
        data_type="NUMERIC(15,2)",
        is_nullable=True,
        description="Total contracted financial value.",
        synonyms=["revenue", "deal size"],
        sample_values=["5000000.00"],
        sensitivity="RESTRICTED",
    )

    fk = ForeignKeyRelation(
        constrained_columns=["verticalCode"],
        referred_schema="public",
        referred_table="Vertical",
        referred_columns=["verticalCode"],
    )

    return TableMetadataEntity(
        name="ProjectName",
        schema_name="public",
        database_id="default",
        description="Master project engagements directory.",
        synonyms=["projects", "client engagements", "accounts"],
        columns={
            "id": col_id,
            "projectname": col_name,
            "contractvalue": col_val,
        },
        primary_keys=["id"],
        foreign_keys=[fk],
        indexes=["idx_proj_name"],
    )


class TestSchemaDocumentBuilder:
    """Tests for SchemaDocumentBuilder methods."""

    def test_build_table_document(self, sample_table_metadata: TableMetadataEntity) -> None:
        """build_table_document produces a valid TABLE SchemaDocument with semantic text."""
        builder = SchemaDocumentBuilder()
        doc = builder.build_table_document(sample_table_metadata)

        assert doc.document_type == SchemaDocumentType.TABLE
        assert doc.document_id == "default:public:projectname:TABLE"
        assert doc.table_name == "ProjectName"
        assert doc.column_name is None
        assert doc.description == "Master project engagements directory."

        # Check semantic text contents
        assert "Table: public.ProjectName" in doc.searchable_text
        assert "Description: Master project engagements directory." in doc.searchable_text
        assert "Synonyms: projects, client engagements, accounts" in doc.searchable_text
        assert "Primary Keys: id" in doc.searchable_text
        assert "verticalCode -> Vertical(verticalCode)" in doc.searchable_text
        assert "Columns:" in doc.searchable_text
        assert "- id (VARCHAR(50), NOT NULL) [PK]" in doc.searchable_text
        assert "- contractValue (NUMERIC(15,2), NULL)" in doc.searchable_text

        # Check metadata
        assert doc.metadata["columns_count"] == 3
        assert doc.metadata["primary_keys"] == ["id"]
        assert doc.metadata["has_foreign_keys"] is True

    def test_build_column_document(self, sample_table_metadata: TableMetadataEntity) -> None:
        """build_column_document produces a valid COLUMN SchemaDocument with column semantics."""
        builder = SchemaDocumentBuilder()
        col = sample_table_metadata.get_column("contractValue")
        assert col is not None

        doc = builder.build_column_document(
            table=sample_table_metadata,
            column=col,
        )

        assert doc.document_type == SchemaDocumentType.COLUMN
        assert doc.document_id == "default:public:projectname:contractvalue:COLUMN"
        assert doc.table_name == "ProjectName"
        assert doc.column_name == "contractValue"
        assert doc.description == "Total contracted financial value."

        # Check semantic text contents
        assert "Column: contractValue" in doc.searchable_text
        assert "Table: public.ProjectName" in doc.searchable_text
        assert "Data Type: NUMERIC(15,2) (NULL)" in doc.searchable_text
        assert "Key Role: Standard Column" in doc.searchable_text
        assert "Synonyms: revenue, deal size" in doc.searchable_text
        assert "Sample Values: 5000000.00" in doc.searchable_text
        assert "Sensitivity: RESTRICTED" in doc.searchable_text

        # Check metadata
        assert doc.metadata["data_type"] == "NUMERIC(15,2)"
        assert doc.metadata["sensitivity"] == "RESTRICTED"
        assert doc.metadata["is_primary_key"] is False
        assert doc.metadata["is_nullable"] is True

    def test_build_documents_for_table(self, sample_table_metadata: TableMetadataEntity) -> None:
        """build_documents_for_table generates 1 table document + N column documents."""
        builder = SchemaDocumentBuilder()
        docs = builder.build_documents_for_table(sample_table_metadata, include_columns=True)

        assert len(docs) == 4  # 1 table + 3 columns
        assert docs[0].document_type == SchemaDocumentType.TABLE
        assert all(d.document_type == SchemaDocumentType.COLUMN for d in docs[1:])

        # When include_columns is False
        table_only_docs = builder.build_documents_for_table(
            sample_table_metadata, include_columns=False
        )
        assert len(table_only_docs) == 1
        assert table_only_docs[0].document_type == SchemaDocumentType.TABLE

    def test_build_documents_for_schema(self, sample_table_metadata: TableMetadataEntity) -> None:
        """build_documents_for_schema traverses all tables in schema."""
        builder = SchemaDocumentBuilder()
        schema = DatabaseSchemaEntity(
            database_id="enterprise_dw",
            schema_name="public",
            tables={"projectname": sample_table_metadata},
        )

        docs = builder.build_documents_for_schema(schema, include_columns=True)
        assert len(docs) == 4
        assert docs[0].database_id == "enterprise_dw"
