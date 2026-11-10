"""
Unit tests for EnterpriseMetadataCatalog and hybrid schema enrichment.

Verifies:
    1. Pre-configured enterprise domain metadata lookup.
    2. Dynamic registration and overriding of table metadata.
    3. Hybrid enrichment preserves physical facts and decorates descriptions/synonyms/sensitivity.
    4. Strict invariant: Non-existent physical tables/columns are never created by the catalog.
"""
import pytest

from text_to_sql.catalog import (
    ColumnBusinessMetadata,
    EnterpriseMetadataCatalog,
    TableBusinessMetadata,
)
from text_to_sql import (
    ColumnMetadataEntity,
    DatabaseSchemaEntity,
    TableMetadataEntity,
)


@pytest.fixture
def sample_physical_schema() -> DatabaseSchemaEntity:
    """Fixture providing a raw introspected schema with minimal physical facts."""
    emp_cols = {
        "employeemailid": ColumnMetadataEntity(
            name="employeeMailId",
            data_type="VARCHAR(255)",
            is_nullable=False,
            is_primary_key=True,
        ),
        "employeename": ColumnMetadataEntity(
            name="employeeName",
            data_type="VARCHAR(150)",
            is_nullable=False,
        ),
        "pannumber": ColumnMetadataEntity(
            name="panNumber",
            data_type="VARCHAR(20)",
            is_nullable=True,
        ),
    }

    emp_table = TableMetadataEntity(
        name="EmployeeInformation",
        columns=emp_cols,
        primary_keys=["employeeMailId"],
    )

    proj_cols = {
        "id": ColumnMetadataEntity(
            name="id",
            data_type="VARCHAR(50)",
            is_primary_key=True,
        ),
        "contractvalue": ColumnMetadataEntity(
            name="contractValue",
            data_type="NUMERIC(15,2)",
        ),
    }

    proj_table = TableMetadataEntity(
        name="ProjectName",
        columns=proj_cols,
        primary_keys=["id"],
    )

    return DatabaseSchemaEntity(
        database_id="enterprise_dw",
        schema_name="public",
        tables={
            "employeeinformation": emp_table,
            "projectname": proj_table,
        },
    )


class TestEnterpriseMetadataCatalog:
    """Tests for metadata catalog retrieval, registration, and schema enrichment."""

    def test_default_catalog_lookup(self) -> None:
        """Default catalog contains metadata for core enterprise tables."""
        catalog = EnterpriseMetadataCatalog()

        emp_meta = catalog.get_table_metadata("EmployeeInformation")
        assert emp_meta is not None
        assert "employee" in emp_meta.synonyms
        assert "employeemailid" in emp_meta.columns
        assert emp_meta.columns["employeemailid"].sensitivity == "INTERNAL"
        assert emp_meta.columns["pannumber"].sensitivity == "CONFIDENTIAL"

        # Case-insensitivity
        assert catalog.get_table_metadata("EMPLOYEEINFORMATION") == emp_meta
        assert catalog.get_table_metadata("unknown_table") is None

    def test_register_and_override_metadata(self) -> None:
        """register_table_metadata adds new table and updates catalog."""
        catalog = EnterpriseMetadataCatalog()

        catalog.register_table_metadata(
            table_name="CustomTable",
            description="Custom domain table",
            synonyms=["custom", "sample"],
            columns={
                "customcol": ColumnBusinessMetadata(
                    description="Custom column description",
                    synonyms=["col_alias"],
                    sensitivity="RESTRICTED",
                )
            },
        )

        meta = catalog.get_table_metadata("CustomTable")
        assert meta is not None
        assert meta.description == "Custom domain table"
        assert "custom" in meta.synonyms
        assert meta.columns["customcol"].sensitivity == "RESTRICTED"

    def test_enrich_schema_decorates_tables_and_columns(
        self, sample_physical_schema: DatabaseSchemaEntity
    ) -> None:
        """enrich_schema attaches descriptions, synonyms, samples, and sensitivity."""
        catalog = EnterpriseMetadataCatalog()
        enriched = catalog.enrich_schema(sample_physical_schema)

        # 1. Verify EmployeeInformation enriched
        emp_table = enriched.get_table("EmployeeInformation")
        assert emp_table is not None
        assert emp_table.description is not None
        assert "workforce" in emp_table.synonyms

        # Check column enrichment
        email_col = emp_table.get_column("employeeMailId")
        assert email_col is not None
        assert email_col.description is not None
        assert email_col.sensitivity == "INTERNAL"
        assert len(email_col.sample_values) > 0
        assert "worker email" in email_col.synonyms

        # Check confidential column classification
        pan_col = emp_table.get_column("panNumber")
        assert pan_col is not None
        assert pan_col.sensitivity == "CONFIDENTIAL"
        assert "tax id" in pan_col.synonyms

        # 2. Verify ProjectName financial column classification
        proj_table = enriched.get_table("ProjectName")
        assert proj_table is not None
        contract_col = proj_table.get_column("contractValue")
        assert contract_col is not None
        assert contract_col.sensitivity == "RESTRICTED"
        assert "revenue" in contract_col.synonyms

        # 3. Verify physical attributes were preserved
        assert email_col.is_primary_key is True
        assert email_col.is_nullable is False
        assert email_col.data_type == "VARCHAR(255)"

    def test_enrich_schema_never_invents_fictitious_columns(
        self, sample_physical_schema: DatabaseSchemaEntity
    ) -> None:
        """Columns present in catalog but missing from physical database are NOT added."""
        catalog = EnterpriseMetadataCatalog()

        # Catalog has passportNumber, fixedCtc, variableCtc for EmployeeInformation
        # but sample_physical_schema only has employeeMailId, employeeName, panNumber
        enriched = catalog.enrich_schema(sample_physical_schema)
        emp_table = enriched.get_table("EmployeeInformation")
        assert emp_table is not None

        assert emp_table.has_column("employeeMailId") is True
        assert emp_table.has_column("employeeName") is True
        assert emp_table.has_column("panNumber") is True

        # Non-introspected columns MUST NOT be present
        assert emp_table.has_column("passportNumber") is False
        assert emp_table.has_column("fixedCtc") is False
        assert emp_table.has_column("variableCtc") is False
        assert len(emp_table.columns) == 3

    def test_enrich_schema_preserves_existing_descriptions(self) -> None:
        """Existing descriptions on table or column entities are preserved."""
        table = TableMetadataEntity(
            name="EmployeeInformation",
            description="Existing custom table description",
            columns={
                "employeemailid": ColumnMetadataEntity(
                    name="employeeMailId",
                    data_type="VARCHAR(255)",
                    description="Existing custom column description",
                )
            },
        )
        schema = DatabaseSchemaEntity(
            database_id="db",
            tables={"employeeinformation": table},
        )

        catalog = EnterpriseMetadataCatalog()
        enriched = catalog.enrich_schema(schema)

        emp_table = enriched.get_table("EmployeeInformation")
        assert emp_table is not None
        assert emp_table.description == "Existing custom table description"
        col = emp_table.get_column("employeeMailId")
        assert col is not None
        assert col.description == "Existing custom column description"
        # Synonyms and sensitivity should still be enriched
        assert col.sensitivity == "INTERNAL"
        assert "worker email" in col.synonyms
