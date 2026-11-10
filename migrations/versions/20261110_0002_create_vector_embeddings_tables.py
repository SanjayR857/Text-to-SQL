"""create_vector_embeddings_tables

Revision ID: 20261110_0002
Revises: 20261109_0001
Create Date: 2026-11-10 22:50:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261110_0002"
down_revision: Union[str, None] = "20261109_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension is enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # =========================================================================
    # 1. Table: schema_embeddings
    # =========================================================================
    op.create_table(
        "schema_embeddings",
        sa.Column("document_id", sa.String(length=255), primary_key=True, nullable=False),
        sa.Column("document_type", sa.String(length=10), nullable=False),
        sa.Column("database_id", sa.String(length=64), server_default="default", nullable=False),
        sa.Column("schema_name", sa.String(length=64), server_default="public", nullable=False),
        sa.Column("table_name", sa.String(length=128), nullable=False),
        sa.Column("column_name", sa.String(length=128), nullable=True),
        sa.Column("searchable_text", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.String(length=32), server_default="1.0.0", nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "document_type IN ('TABLE', 'COLUMN')",
            name="chk_schema_embeddings_document_type",
        ),
    )

    op.create_index(
        "ix_schema_embeddings_table_name",
        "schema_embeddings",
        ["table_name"],
        unique=False,
    )
    op.create_index(
        "ix_schema_embeddings_content_hash",
        "schema_embeddings",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        "ix_schema_embeddings_table_type",
        "schema_embeddings",
        ["table_name", "document_type"],
        unique=False,
    )
    op.create_index(
        "ix_schema_embeddings_metadata",
        "schema_embeddings",
        ["metadata"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "idx_schema_embeddings_hnsw",
        "schema_embeddings",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    # =========================================================================
    # 2. Table: entity_embeddings
    # =========================================================================
    op.create_table(
        "entity_embeddings",
        sa.Column("document_id", sa.String(length=255), primary_key=True, nullable=False),
        sa.Column("database_id", sa.String(length=64), server_default="default", nullable=False),
        sa.Column("schema_name", sa.String(length=64), server_default="public", nullable=False),
        sa.Column("table_name", sa.String(length=128), nullable=False),
        sa.Column("primary_key_column", sa.String(length=128), nullable=False),
        sa.Column("primary_key_value", sa.String(length=255), nullable=False),
        sa.Column("entity_label", sa.String(length=255), nullable=False),
        sa.Column("searchable_text", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_entity_embeddings_table_name",
        "entity_embeddings",
        ["table_name"],
        unique=False,
    )
    op.create_index(
        "ix_entity_embeddings_content_hash",
        "entity_embeddings",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        "ix_entity_embeddings_table_pk",
        "entity_embeddings",
        ["table_name", "primary_key_value"],
        unique=False,
    )
    op.create_index(
        "ix_entity_embeddings_metadata",
        "entity_embeddings",
        ["metadata"],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "idx_entity_embeddings_hnsw",
        "entity_embeddings",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_table("entity_embeddings")
    op.drop_table("schema_embeddings")
