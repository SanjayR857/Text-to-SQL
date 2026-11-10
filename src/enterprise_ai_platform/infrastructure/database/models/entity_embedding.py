"""
SQLAlchemy 2.x ORM model for entity value embeddings storage.

Represents the 'entity_embeddings' table storing dense vector embeddings,
metadata, and SHA-256 hashes for selective database row values (e.g. project names,
employee directory entries, vertical codes).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from enterprise_ai_platform.infrastructure.database.base import Base


class EntityEmbeddingModel(Base):
    """
    Persisted vector representation of a specific database entity / row.

    Used for exact WHERE-clause filter value matching, typo resolution,
    and semantic entity retrieval.
    """

    __tablename__ = "entity_embeddings"
    __table_args__ = (
        Index("ix_entity_embeddings_table_pk", "table_name", "primary_key_value"),
        Index("ix_entity_embeddings_content_hash", "content_hash"),
        Index("ix_entity_embeddings_metadata", "metadata", postgresql_using="gin"),
        Index(
            "idx_entity_embeddings_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    # Primary key: deterministic ID (e.g. 'default:public:projectname:prj-001:ENTITY')
    document_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Scope
    database_id: Mapped[str] = mapped_column(String(64), nullable=False, default="default")
    schema_name: Mapped[str] = mapped_column(String(64), nullable=False, default="public")
    table_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # Entity identifiers
    primary_key_column: Mapped[str] = mapped_column(String(128), nullable=False)
    primary_key_value: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_label: Mapped[str] = mapped_column(String(255), nullable=False)

    # Content
    searchable_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    # Hash
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # pgvector 1536-dimensional embedding
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)

    # Timestamps
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
