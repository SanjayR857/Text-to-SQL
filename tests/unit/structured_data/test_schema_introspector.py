"""
Unit tests for PostgresSchemaIntrospector.

Tests physical schema extraction, column typing, primary key and foreign key detection,
index reflection, table filtering, and async dispatch.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy import Column, ForeignKey, Index, Integer, MetaData, String, Table, create_engine

from enterprise_ai_platform.domain.structured_data import (
    ColumnMetadataEntity,
    DatabaseSchemaEntity,
    TableMetadataEntity,
)
from enterprise_ai_platform.infrastructure.database.schema_introspector import (
    PostgresSchemaIntrospector,
)


@pytest.fixture
def sqlite_engine():
    """Create an in-memory SQLite database engine with sample tables for introspection."""
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()

    # Table 1: EmployeeInformation
    Table(
        "EmployeeInformation",
        metadata,
        Column("employeeMailId", String(255), primary_key=True),
        Column("employeeName", String(150), nullable=False),
        Column("designation", String(100), nullable=True),
        Column("verticalCode", String(50), nullable=False),
        Index("idx_emp_vertical", "verticalCode"),
    )

    # Table 2: ProjectName
    Table(
        "ProjectName",
        metadata,
        Column("id", String(50), primary_key=True),
        Column("projectName", String(200), nullable=False),
        Column("verticalCode", String(50), nullable=False),
    )

    # Table 3: ProjectDetail (with Foreign Key to ProjectName)
    Table(
        "ProjectDetail",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("projectId", String(50), ForeignKey("ProjectName.id"), nullable=False),
        Column("resourceMailID", String(255), nullable=False),
        Column("allocationPercentage", Integer, nullable=True),
        Index("idx_proj_detail_resource", "resourceMailID"),
    )

    # Table 4: alembic_version (should be ignored by default)
    Table(
        "alembic_version",
        metadata,
        Column("version_num", String(32), primary_key=True),
    )

    metadata.create_all(engine)
    yield engine
    metadata.drop_all(engine)
    engine.dispose()


class TestPostgresSchemaIntrospector:
    """Tests verifying live schema introspection behavior."""

    def test_sync_introspection_extracts_tables_and_columns(self, sqlite_engine) -> None:
        """Introspector extracts tables, columns, types, nullability, and primary keys."""
        introspector = PostgresSchemaIntrospector()
        with sqlite_engine.connect() as conn:
            schema = introspector.introspect_sync(
                conn=conn,
                database_id="test_db",
                schema_name="main",  # SQLite default schema
                version="1.0.0",
            )

        assert isinstance(schema, DatabaseSchemaEntity)
        assert schema.database_id == "test_db"
        assert schema.last_introspected_at is not None

        # Verify alembic_version was ignored
        assert not schema.has_table("alembic_version")

        # Verify EmployeeInformation table
        emp_table = schema.get_table("EmployeeInformation")
        assert emp_table is not None
        assert emp_table.name == "EmployeeInformation"
        assert "employeeMailId" in emp_table.primary_keys

        # Check column metadata
        email_col = emp_table.get_column("employeeMailId")
        assert email_col is not None
        assert email_col.name == "employeeMailId"
        assert email_col.is_primary_key is True
        assert email_col.is_nullable is False

        desig_col = emp_table.get_column("designation")
        assert desig_col is not None
        assert desig_col.is_nullable is True
        assert desig_col.is_primary_key is False

    def test_foreign_key_and_index_detection(self, sqlite_engine) -> None:
        """Introspector accurately identifies foreign keys and index names."""
        introspector = PostgresSchemaIntrospector()
        with sqlite_engine.connect() as conn:
            schema = introspector.introspect_sync(
                conn=conn,
                database_id="test_db",
                schema_name="main",
            )

        detail_table = schema.get_table("ProjectDetail")
        assert detail_table is not None

        # Foreign key validation
        assert len(detail_table.foreign_keys) >= 1
        fk = detail_table.foreign_keys[0]
        assert "projectId" in fk.constrained_columns
        assert fk.referred_table.lower() == "projectname"

        # Check column-level FK annotation
        proj_id_col = detail_table.get_column("projectId")
        assert proj_id_col is not None
        assert proj_id_col.is_foreign_key is True
        assert proj_id_col.foreign_key_target is not None
        assert "projectname" in proj_id_col.foreign_key_target.lower()

        # Indexes
        assert any("idx_proj_detail_resource" in idx for idx in detail_table.indexes)

    def test_target_tables_filtering(self, sqlite_engine) -> None:
        """target_tables restricts introspection strictly to specified tables."""
        introspector = PostgresSchemaIntrospector()
        with sqlite_engine.connect() as conn:
            schema = introspector.introspect_sync(
                conn=conn,
                database_id="test_db",
                schema_name="main",
                target_tables=["EmployeeInformation"],
            )

        assert schema.has_table("EmployeeInformation") is True
        assert schema.has_table("ProjectName") is False
        assert schema.has_table("ProjectDetail") is False
        assert schema.total_tables_count == 1

    def test_custom_ignored_tables(self, sqlite_engine) -> None:
        """Custom ignored_tables set excludes configured tables."""
        introspector = PostgresSchemaIntrospector(
            ignored_tables={"ProjectDetail", "alembic_version"}
        )
        with sqlite_engine.connect() as conn:
            schema = introspector.introspect_sync(
                conn=conn,
                database_id="test_db",
                schema_name="main",
            )

        assert schema.has_table("EmployeeInformation") is True
        assert schema.has_table("ProjectName") is True
        assert schema.has_table("ProjectDetail") is False

    @pytest.mark.asyncio
    async def test_async_introspection_dispatch_with_connection(self) -> None:
        """introspect_async dispatches to run_sync when given an AsyncConnection."""
        introspector = PostgresSchemaIntrospector()
        mock_schema = DatabaseSchemaEntity(
            database_id="mock_db",
            tables={},
        )

        mock_conn = MagicMock()
        mock_conn.run_sync = AsyncMock(return_value=mock_schema)

        result = await introspector.introspect_async(
            engine_or_conn=mock_conn,
            database_id="mock_db",
        )

        assert result == mock_schema
        mock_conn.run_sync.assert_awaited_once()
