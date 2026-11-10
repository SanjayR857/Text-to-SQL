"""
Schema document domain model and granularity specifications.

Encapsulates table-level and column-level schema documents prepared for
vector embedding generation and similarity retrieval in pgvector.
"""
from enum import Enum
import hashlib
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SchemaDocumentType(str, Enum):
    """
    Granularity type of a schema document in the vector store.
    """

    TABLE = "TABLE"
    COLUMN = "COLUMN"


class SchemaDocument(BaseModel):
    """
    Canonical document representation of a database table or column for vector search.

    Maintains deterministic identity, full-text searchable representation,
    hash-based change detection, and structured metadata for hybrid retrieval.
    """

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(
        ...,
        description="Deterministic document identifier: '{database_id}:{schema_name}:{table_name}[:{column_name}]:{document_type}'",
    )
    document_type: SchemaDocumentType = Field(
        ...,
        description="Granularity of the document (TABLE or COLUMN)",
    )
    database_id: str = Field(
        default="default",
        description="Logical database identifier",
    )
    schema_name: str = Field(
        default="public",
        description="PostgreSQL schema name",
    )
    table_name: str = Field(
        ...,
        description="Physical table name",
    )
    column_name: str | None = Field(
        default=None,
        description="Physical column name (required for COLUMN, None for TABLE)",
    )
    searchable_text: str = Field(
        ...,
        description="Rich natural language content embedded into vector space",
    )
    description: str = Field(
        default="",
        description="Curated business description or domain commentary",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key-value metadata for vector store filtering and synchronization",
    )
    content_hash: str = Field(
        ...,
        description="SHA-256 hash of searchable content and structural attributes for change detection",
    )
    schema_version: str = Field(
        default="1.0.0",
        description="Schema or catalog version tag",
    )

    @model_validator(mode="after")
    def validate_document_consistency(self) -> "SchemaDocument":
        """
        Validate consistency between document_type, column_name, and document_id.
        """
        if self.document_type == SchemaDocumentType.TABLE:
            if self.column_name is not None and self.column_name.strip() != "":
                raise ValueError("TABLE document must not have a column_name specified")
        elif self.document_type == SchemaDocumentType.COLUMN:
            if not self.column_name or not self.column_name.strip():
                raise ValueError("COLUMN document must have a non-empty column_name specified")

        expected_id = self.build_document_id(
            database_id=self.database_id,
            schema_name=self.schema_name,
            table_name=self.table_name,
            document_type=self.document_type,
            column_name=self.column_name,
        )

        if self.document_id != expected_id:
            raise ValueError(
                f"Invalid document_id '{self.document_id}'. Expected deterministic ID '{expected_id}'"
            )

        return self

    @staticmethod
    def build_document_id(
        database_id: str,
        schema_name: str,
        table_name: str,
        document_type: SchemaDocumentType,
        column_name: str | None = None,
    ) -> str:
        """
        Generate deterministic document ID.

        Format:
            TABLE:  {database_id}:{schema_name}:{table_name}:TABLE
            COLUMN: {database_id}:{schema_name}:{table_name}:{column_name}:COLUMN

        Args:
            database_id: Database identifier.
            schema_name: PostgreSQL schema name.
            table_name: Physical table name.
            document_type: Granularity enum (TABLE or COLUMN).
            column_name: Column name if document_type is COLUMN.

        Returns:
            Deterministic string identifier.
        """
        db = database_id.strip().lower()
        schema = schema_name.strip().lower()
        tbl = table_name.strip().lower()

        if document_type == SchemaDocumentType.COLUMN:
            if not column_name:
                raise ValueError("column_name is required when document_type is COLUMN")
            col = column_name.strip().lower()
            return f"{db}:{schema}:{tbl}:{col}:COLUMN"
        return f"{db}:{schema}:{tbl}:TABLE"

    @staticmethod
    def compute_content_hash(text: str, extra: str = "") -> str:
        """
        Compute SHA-256 hash of searchable text and optional structural metadata.

        Args:
            text: Primary searchable text string.
            extra: Optional additional structural text or configuration.

        Returns:
            Hex-encoded SHA-256 string.
        """
        raw = f"{text.strip()}::{extra.strip()}" if extra else text.strip()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def create_table_document(
        cls,
        table_name: str,
        searchable_text: str,
        description: str = "",
        database_id: str = "default",
        schema_name: str = "public",
        schema_version: str = "1.0.0",
        extra_metadata: dict[str, Any] | None = None,
    ) -> "SchemaDocument":
        """
        Factory to create a canonical table-level SchemaDocument.

        Args:
            table_name: Physical table name.
            searchable_text: Semantic text for embedding.
            description: Business description.
            database_id: Database ID.
            schema_name: PostgreSQL schema name.
            schema_version: Schema version string.
            extra_metadata: Optional additional metadata fields.

        Returns:
            Instantiated and validated SchemaDocument.
        """
        doc_id = cls.build_document_id(
            database_id=database_id,
            schema_name=schema_name,
            table_name=table_name,
            document_type=SchemaDocumentType.TABLE,
        )
        content_hash = cls.compute_content_hash(searchable_text, extra=description)

        metadata: dict[str, Any] = {
            "database_id": database_id.strip().lower(),
            "schema_name": schema_name.strip().lower(),
            "table_name": table_name.strip(),
            "document_type": SchemaDocumentType.TABLE.value,
            "column_name": None,
            "content_hash": content_hash,
            "schema_version": schema_version,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        return cls(
            document_id=doc_id,
            document_type=SchemaDocumentType.TABLE,
            database_id=database_id,
            schema_name=schema_name,
            table_name=table_name,
            column_name=None,
            searchable_text=searchable_text,
            description=description,
            metadata=metadata,
            content_hash=content_hash,
            schema_version=schema_version,
        )

    @classmethod
    def create_column_document(
        cls,
        table_name: str,
        column_name: str,
        searchable_text: str,
        description: str = "",
        database_id: str = "default",
        schema_name: str = "public",
        schema_version: str = "1.0.0",
        data_type: str = "",
        extra_metadata: dict[str, Any] | None = None,
    ) -> "SchemaDocument":
        """
        Factory to create a canonical column-level SchemaDocument.

        Args:
            table_name: Physical table name.
            column_name: Physical column name.
            searchable_text: Semantic text for embedding.
            description: Business description.
            database_id: Database ID.
            schema_name: PostgreSQL schema name.
            schema_version: Schema version string.
            data_type: SQL data type for metadata tagging.
            extra_metadata: Optional additional metadata fields.

        Returns:
            Instantiated and validated SchemaDocument.
        """
        doc_id = cls.build_document_id(
            database_id=database_id,
            schema_name=schema_name,
            table_name=table_name,
            document_type=SchemaDocumentType.COLUMN,
            column_name=column_name,
        )
        content_hash = cls.compute_content_hash(
            searchable_text,
            extra=f"{description}::{data_type}",
        )

        metadata: dict[str, Any] = {
            "database_id": database_id.strip().lower(),
            "schema_name": schema_name.strip().lower(),
            "table_name": table_name.strip(),
            "document_type": SchemaDocumentType.COLUMN.value,
            "column_name": column_name.strip(),
            "data_type": data_type,
            "content_hash": content_hash,
            "schema_version": schema_version,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        return cls(
            document_id=doc_id,
            document_type=SchemaDocumentType.COLUMN,
            database_id=database_id,
            schema_name=schema_name,
            table_name=table_name,
            column_name=column_name,
            searchable_text=searchable_text,
            description=description,
            metadata=metadata,
            content_hash=content_hash,
            schema_version=schema_version,
        )
