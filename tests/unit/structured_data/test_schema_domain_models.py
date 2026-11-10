"""
Unit tests for canonical schema domain models and SchemaDocument contracts.

Verifies:
    1. SchemaDocument creation, validation, deterministic IDs, and hashing.
    2. ColumnMetadataEntity, TableMetadataEntity, and ForeignKeyRelation behavior.
    3. DatabaseSchemaEntity hierarchical lookups, counts, and case-insensitivity.
    4. Domain model immutability across all entities.
"""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from enterprise_ai_platform.domain.structured_data import (
    ColumnMetadataEntity,
    DatabaseSchemaEntity,
    ForeignKeyRelation,
    SchemaDocument,
    SchemaDocumentType,
    TableMetadataEntity,
)


class TestSchemaDocument:
    """Tests for SchemaDocument identity, validation, and factory methods."""

    def test_build_document_id_for_table(self) -> None:
        """Deterministic table document ID formats as database:schema:table:TABLE."""
        doc_id = SchemaDocument.build_document_id(
            database_id="MainDb",
            schema_name="Public",
            table_name="EmployeeInformation",
            document_type=SchemaDocumentType.TABLE,
        )
        assert doc_id == "maindb:public:employeeinformation:TABLE"

    def test_build_document_id_for_column(self) -> None:
        """Deterministic column document ID formats as database:schema:table:column:COLUMN."""
        doc_id = SchemaDocument.build_document_id(
            database_id="MainDb",
            schema_name="Public",
            table_name="EmployeeInformation",
            document_type=SchemaDocumentType.COLUMN,
            column_name="EmployeeMailId",
        )
        assert doc_id == "maindb:public:employeeinformation:employeemailid:COLUMN"

    def test_build_document_id_column_without_name_raises(self) -> None:
        """Building COLUMN document ID without column name raises ValueError."""
        with pytest.raises(ValueError, match="column_name is required"):
            SchemaDocument.build_document_id(
                database_id="default",
                schema_name="public",
                table_name="EmployeeInformation",
                document_type=SchemaDocumentType.COLUMN,
                column_name=None,
            )

    def test_compute_content_hash_deterministic(self) -> None:
        """Content hash produces consistent SHA-256 for identical inputs."""
        hash1 = SchemaDocument.compute_content_hash("Table of employees", extra="HR Domain")
        hash2 = SchemaDocument.compute_content_hash("Table of employees", extra="HR Domain")
        hash3 = SchemaDocument.compute_content_hash("Table of projects", extra="HR Domain")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64

    def test_create_table_document_factory(self) -> None:
        """Factory creates valid, immutable table SchemaDocument with metadata."""
        doc = SchemaDocument.create_table_document(
            table_name="EmployeeInformation",
            searchable_text="Table EmployeeInformation stores core worker profiles and designations.",
            description="Core employee registry.",
            database_id="default",
            schema_name="public",
            extra_metadata={"vertical": "HR"},
        )

        assert doc.document_id == "default:public:employeeinformation:TABLE"
        assert doc.document_type == SchemaDocumentType.TABLE
        assert doc.table_name == "EmployeeInformation"
        assert doc.column_name is None
        assert doc.metadata["vertical"] == "HR"
        assert doc.metadata["document_type"] == "TABLE"
        assert doc.metadata["table_name"] == "EmployeeInformation"
        assert doc.content_hash == SchemaDocument.compute_content_hash(
            doc.searchable_text, extra=doc.description
        )

        # Immutability
        with pytest.raises(ValidationError):
            doc.table_name = "MutatedTable"  # type: ignore[misc]

    def test_create_column_document_factory(self) -> None:
        """Factory creates valid, immutable column SchemaDocument with metadata."""
        doc = SchemaDocument.create_column_document(
            table_name="EmployeeInformation",
            column_name="employeeMailId",
            searchable_text="Column employeeMailId: Primary corporate email address for employee.",
            description="Corporate email address.",
            data_type="VARCHAR(255)",
            database_id="default",
            schema_name="public",
            extra_metadata={"sensitivity": "INTERNAL"},
        )

        assert doc.document_id == "default:public:employeeinformation:employeemailid:COLUMN"
        assert doc.document_type == SchemaDocumentType.COLUMN
        assert doc.table_name == "EmployeeInformation"
        assert doc.column_name == "employeeMailId"
        assert doc.metadata["data_type"] == "VARCHAR(255)"
        assert doc.metadata["sensitivity"] == "INTERNAL"
        assert doc.metadata["document_type"] == "COLUMN"

        # Immutability
        with pytest.raises(ValidationError):
            doc.column_name = "mutated_column"  # type: ignore[misc]

    def test_table_document_with_column_name_fails_validation(self) -> None:
        """TABLE document having column_name raises validation error."""
        with pytest.raises(ValidationError, match="TABLE document must not have a column_name"):
            SchemaDocument(
                document_id="default:public:employees:TABLE",
                document_type=SchemaDocumentType.TABLE,
                database_id="default",
                schema_name="public",
                table_name="employees",
                column_name="some_col",
                searchable_text="Text",
                content_hash="dummy_hash",
            )

    def test_column_document_without_column_name_fails_validation(self) -> None:
        """COLUMN document without column_name raises validation error."""
        with pytest.raises(ValidationError, match="COLUMN document must have a non-empty column_name"):
            SchemaDocument(
                document_id="default:public:employees::COLUMN",
                document_type=SchemaDocumentType.COLUMN,
                database_id="default",
                schema_name="public",
                table_name="employees",
                column_name=None,
                searchable_text="Text",
                content_hash="dummy_hash",
            )

    def test_mismatched_document_id_fails_validation(self) -> None:
        """Document with mismatched document_id raises validation error."""
        with pytest.raises(ValidationError, match="Invalid document_id"):
            SchemaDocument(
                document_id="wrong_id_pattern",
                document_type=SchemaDocumentType.TABLE,
                database_id="default",
                schema_name="public",
                table_name="employees",
                column_name=None,
                searchable_text="Text",
                content_hash="dummy_hash",
            )


class TestTableMetadataEntity:
    """Tests for TableMetadataEntity, ColumnMetadataEntity, and ForeignKeyRelation."""

    def test_column_metadata_defaults_and_immutability(self) -> None:
        """ColumnMetadataEntity defaults are applied and entity is immutable."""
        col = ColumnMetadataEntity(
            name="employeeName",
            data_type="VARCHAR(150)",
        )
        assert col.name == "employeeName"
        assert col.data_type == "VARCHAR(150)"
        assert col.is_nullable is True
        assert col.is_primary_key is False
        assert col.is_foreign_key is False
        assert col.foreign_key_target is None
        assert col.synonyms == []
        assert col.sample_values == []

        with pytest.raises(ValidationError):
            col.name = "changed"  # type: ignore[misc]

    def test_foreign_key_relation(self) -> None:
        """ForeignKeyRelation captures multi-column or single-column FK definitions."""
        fk = ForeignKeyRelation(
            constrained_columns=["departmentId"],
            referred_schema="public",
            referred_table="Departments",
            referred_columns=["id"],
        )
        assert fk.constrained_columns == ["departmentId"]
        assert fk.referred_table == "Departments"
        assert fk.referred_columns == ["id"]

        with pytest.raises(ValidationError):
            fk.referred_table = "Other"  # type: ignore[misc]

    def test_table_metadata_case_insensitive_lookups(self) -> None:
        """TableMetadataEntity provides case-insensitive column lookup and listing."""
        col_id = ColumnMetadataEntity(
            name="employeeId",
            data_type="INTEGER",
            is_nullable=False,
            is_primary_key=True,
        )
        col_name = ColumnMetadataEntity(
            name="employeeName",
            data_type="VARCHAR(200)",
            description="Full legal name",
            synonyms=["staff name", "worker name"],
        )

        table = TableMetadataEntity(
            name="EmployeeInformation",
            schema_name="public",
            description="Master employee directory",
            synonyms=["Staff", "Personnel"],
            columns={
                "employeeid": col_id,
                "employeename": col_name,
            },
            primary_keys=["employeeId"],
        )

        # Case-insensitive column retrieval
        assert table.get_column("employeeid") == col_id
        assert table.get_column("EMPLOYEEID") == col_id
        assert table.get_column("EmployeeName") == col_name
        assert table.get_column("non_existent") is None

        # Check existence
        assert table.has_column("employeeName") is True
        assert table.has_column("unknown") is False
        assert table.has_column("") is False

        # Preserved casing column list
        col_names = table.list_column_names()
        assert "employeeId" in col_names
        assert "employeeName" in col_names


class TestDatabaseSchemaEntity:
    """Tests for DatabaseSchemaEntity aggregate lookups and inventory metrics."""

    def test_database_schema_lookups_and_counts(self) -> None:
        """DatabaseSchemaEntity correctly looks up tables and columns across tables."""
        col_emp = ColumnMetadataEntity(
            name="employeeMailId",
            data_type="VARCHAR(255)",
            is_primary_key=True,
        )
        emp_table = TableMetadataEntity(
            name="EmployeeInformation",
            columns={"employeemailid": col_emp},
            primary_keys=["employeeMailId"],
        )

        col_att = ColumnMetadataEntity(
            name="attendanceDate",
            data_type="DATE",
        )
        att_table = TableMetadataEntity(
            name="OfficeAttendance",
            columns={"attendancedate": col_att},
        )

        now = datetime.now(timezone.utc)
        schema = DatabaseSchemaEntity(
            database_id="enterprise_dw",
            schema_name="public",
            version="2.0.0",
            tables={
                "employeeinformation": emp_table,
                "officeattendance": att_table,
            },
            last_introspected_at=now,
            description="Enterprise Data Warehouse Operational Schema",
        )

        assert schema.total_tables_count == 2
        assert schema.total_columns_count == 2
        assert schema.last_introspected_at == now

        # Case-insensitive table lookup
        assert schema.has_table("EmployeeInformation") is True
        assert schema.has_table("EMPLOYEEINFORMATION") is True
        assert schema.has_table("Scoreboard") is False
        assert schema.has_table("") is False

        # Table retrieval
        assert schema.get_table("employeeinformation") == emp_table
        assert schema.get_table("OFFICEATTENDANCE") == att_table
        assert schema.get_table("Unknown") is None

        # Cross-table column lookup
        col = schema.get_column("EmployeeInformation", "employeeMailId")
        assert col == col_emp
        assert schema.get_column("EmployeeInformation", "NON_EXISTENT") is None
        assert schema.get_column("NonExistentTable", "col") is None

        # Preserved table name list
        table_names = schema.list_table_names()
        assert "EmployeeInformation" in table_names
        assert "OfficeAttendance" in table_names

        # Immutability
        with pytest.raises(ValidationError):
            schema.database_id = "other_dw"  # type: ignore[misc]
