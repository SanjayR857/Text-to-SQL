"""
Unit tests for SQLAlchemy 2.0 ORM models: SchemaEmbeddingModel & EntityEmbeddingModel.

Verifies declarative table schemas, column types, constraints, and HNSW indexes.
"""
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
import pytest
from sqlalchemy import Index
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from enterprise_ai_platform.core.database import Base
from enterprise_ai_platform.text_to_sql.models import (
    EntityEmbeddingModel,
    SchemaEmbeddingModel,
)


class TestEmbeddingSQLAlchemyModels:
    """Test suite for declarative vector embedding ORM models."""

    def test_models_registered_in_declarative_base(self) -> None:
        """Verify both models are registered under Base.metadata."""
        assert "schema_embeddings" in Base.metadata.tables
        assert "entity_embeddings" in Base.metadata.tables

    def test_schema_embedding_columns_and_types(self) -> None:
        """Verify schema_embeddings table structure, primary key, and column types."""
        table = SchemaEmbeddingModel.__table__

        assert table.c.document_id.primary_key is True
        assert isinstance(table.c.embedding.type, Vector)
        assert table.c.embedding.type.dim == 1536
        assert isinstance(table.c.metadata.type, postgresql.JSONB)
        assert isinstance(table.c.created_at.type, postgresql.TIMESTAMP)
        assert isinstance(table.c.updated_at.type, postgresql.TIMESTAMP)

        # Check required columns are not nullable
        assert table.c.document_id.nullable is False
        assert table.c.document_type.nullable is False
        assert table.c.table_name.nullable is False
        assert table.c.content_hash.nullable is False
        assert table.c.searchable_text.nullable is False

        # column_name is nullable for TABLE-level documents
        assert table.c.column_name.nullable is True

    def test_entity_embedding_columns_and_types(self) -> None:
        """Verify entity_embeddings table structure, primary key, and column types."""
        table = EntityEmbeddingModel.__table__

        assert table.c.document_id.primary_key is True
        assert isinstance(table.c.embedding.type, Vector)
        assert table.c.embedding.type.dim == 1536
        assert isinstance(table.c.metadata.type, postgresql.JSONB)
        assert isinstance(table.c.created_at.type, postgresql.TIMESTAMP)
        assert isinstance(table.c.updated_at.type, postgresql.TIMESTAMP)

        # Check entity-specific columns
        assert table.c.primary_key_column.nullable is False
        assert table.c.primary_key_value.nullable is False
        assert table.c.entity_label.nullable is False
        assert table.c.searchable_text.nullable is False

    def test_schema_embedding_hnsw_and_secondary_indexes(self) -> None:
        """Verify HNSW vector index and secondary indexes are declared in __table_args__."""
        table = SchemaEmbeddingModel.__table__
        index_names = {idx.name for idx in table.indexes}

        assert "idx_schema_embeddings_hnsw" in index_names
        assert "ix_schema_embeddings_table_type" in index_names
        assert "ix_schema_embeddings_content_hash" in index_names
        assert "ix_schema_embeddings_metadata" in index_names

        # Verify HNSW index parameters
        hnsw_idx = next(idx for idx in table.indexes if idx.name == "idx_schema_embeddings_hnsw")
        assert hnsw_idx.dialect_options["postgresql"]["using"] == "hnsw"
        assert hnsw_idx.dialect_options["postgresql"]["with"] == {"m": 16, "ef_construction": 64}
        assert hnsw_idx.dialect_options["postgresql"]["ops"] == {"embedding": "vector_cosine_ops"}

    def test_entity_embedding_hnsw_and_secondary_indexes(self) -> None:
        """Verify HNSW vector index and secondary indexes for entity_embeddings."""
        table = EntityEmbeddingModel.__table__
        index_names = {idx.name for idx in table.indexes}

        assert "idx_entity_embeddings_hnsw" in index_names
        assert "ix_entity_embeddings_table_pk" in index_names
        assert "ix_entity_embeddings_content_hash" in index_names
        assert "ix_entity_embeddings_metadata" in index_names

        # Verify HNSW index parameters
        hnsw_idx = next(idx for idx in table.indexes if idx.name == "idx_entity_embeddings_hnsw")
        assert hnsw_idx.dialect_options["postgresql"]["using"] == "hnsw"
        assert hnsw_idx.dialect_options["postgresql"]["with"] == {"m": 16, "ef_construction": 64}
        assert hnsw_idx.dialect_options["postgresql"]["ops"] == {"embedding": "vector_cosine_ops"}

    def test_ddl_compilation_without_raw_sql(self) -> None:
        """Verify SQLAlchemy compiles complete DDL including vector types and HNSW indexes."""
        dialect = postgresql.dialect()

        schema_ddl = str(CreateTable(SchemaEmbeddingModel.__table__).compile(dialect=dialect))
        assert "CREATE TABLE schema_embeddings" in schema_ddl
        assert "embedding VECTOR(1536) NOT NULL" in schema_ddl
        assert "metadata JSONB NOT NULL" in schema_ddl

        entity_ddl = str(CreateTable(EntityEmbeddingModel.__table__).compile(dialect=dialect))
        assert "CREATE TABLE entity_embeddings" in entity_ddl
        assert "embedding VECTOR(1536) NOT NULL" in entity_ddl
        assert "primary_key_column VARCHAR(128) NOT NULL" in entity_ddl

        # Verify HNSW DDL compilation
        hnsw_schema = next(idx for idx in SchemaEmbeddingModel.__table__.indexes if idx.name == "idx_schema_embeddings_hnsw")
        hnsw_schema_ddl = str(CreateIndex(hnsw_schema).compile(dialect=dialect))
        assert "USING hnsw (embedding vector_cosine_ops)" in hnsw_schema_ddl
        assert "WITH (m = 16, ef_construction = 64)" in hnsw_schema_ddl

    def test_model_instantiation(self) -> None:
        """Verify ORM models can be instantiated as valid Python objects."""
        now = datetime.now(timezone.utc)
        dummy_vector = [0.1] * 1536

        schema_record = SchemaEmbeddingModel(
            document_id="default:public:projectname:TABLE",
            document_type="TABLE",
            database_id="default",
            schema_name="public",
            table_name="ProjectName",
            column_name=None,
            searchable_text="Table ProjectName",
            description="Projects",
            metadata_={"sensitivity": "INTERNAL"},
            content_hash="abc123hash",
            schema_version="1.0.0",
            embedding=dummy_vector,
            created_at=now,
            updated_at=now,
        )
        assert schema_record.document_id == "default:public:projectname:TABLE"
        assert len(schema_record.embedding) == 1536

        entity_record = EntityEmbeddingModel(
            document_id="default:public:projectname:prj-001:ENTITY",
            database_id="default",
            schema_name="public",
            table_name="ProjectName",
            primary_key_column="ProjectId",
            primary_key_value="PRJ-001",
            entity_label="Project Apollo",
            searchable_text="Entity Project Apollo",
            metadata_={"vertical": "BFSI"},
            content_hash="xyz789hash",
            embedding=dummy_vector,
            created_at=now,
            updated_at=now,
        )
        assert entity_record.primary_key_value == "PRJ-001"
        assert entity_record.entity_label == "Project Apollo"
