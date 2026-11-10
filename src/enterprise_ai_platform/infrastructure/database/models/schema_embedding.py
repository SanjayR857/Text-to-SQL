"""
SQLAlchemy 2.x ORM model for pgvector schema embeddings storage.

Represents the 'schema_embeddings' table storing dense vector embeddings,
metadata, and SHA-256 content hashes for database tables and columns.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from enterprise_ai_platform.infrastructure.database.base import Base


class SchemaEmbeddingModel(Base):
    """
    Persisted vector representation of a database table or column.

    Enables high-performance cosine similarity retrieval, HNSW indexing,
    and metadata filtering via pgvector.
    """

    __tablename__ = "schema_embeddings"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('TABLE', 'COLUMN')",
            name="chk_schema_embeddings_document_type",
        ),
        Index("ix_schema_embeddings_table_type", "table_name", "document_type"),
        Index("ix_schema_embeddings_content_hash", "content_hash"),
        Index("ix_schema_embeddings_metadata", "metadata", postgresql_using="gin"),
        Index(
            "idx_schema_embeddings_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    # Primary key: deterministic ID (e.g., 'default:public:employeeinformation:TABLE')
    document_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Granularity: 'TABLE' or 'COLUMN'
    document_type: Mapped[str] = mapped_column(String(10), nullable=False)

    # Scope hierarchy
    database_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    schema_name: Mapped[str] = mapped_column(String(64), nullable=False, default="public")
    table_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    column_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Content
    searchable_text: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Metadata dictionary for JSONB filtering
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    # Change detection and versioning
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")

    # pgvector 1536-dimensional embedding
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
