"""
Entity value document models, table configurations, and retrieval intent enums.

Defines the domain contracts for selective row/entity embeddings (e.g. project names,
employee identities, vertical codes) used for exact WHERE filter value disambiguation.
"""
from enum import Enum
import hashlib
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RetrievalIntent(str, Enum):
    """
    Classified intent of a user's natural language database query.
    """

    SCHEMA_ONLY = "SCHEMA_ONLY"    # Pure analytical/structural queries (counts, sums, aggregations)
    ENTITY_ONLY = "ENTITY_ONLY"    # Direct entity lookups (e.g., "Who is John Doe?")
    HYBRID_BOTH = "HYBRID_BOTH"    # Analytical queries naming specific entities (e.g., "Apollo project revenue")


class EntityTableConfig(BaseModel):
    """
    Configuration specifying which table and columns are enabled for selective entity embedding.
    """

    model_config = ConfigDict(frozen=True)

    table_name: str = Field(..., description="Canonical database table name")
    primary_key_column: str = Field(..., description="Primary key column name")
    searchable_columns: list[str] = Field(
        ...,
        description="Whitelisted columns included in the entity's searchable text (strictly non-confidential)",
    )
    label_template: str = Field(
        ...,
        description="String template for human-readable label, e.g. '{projectName} (ID: {id})'",
    )
    vertical_code_column: str | None = Field(
        default=None,
        description="Column name storing the vertical code for RBAC filtering, if applicable",
    )
    project_id_column: str | None = Field(
        default=None,
        description="Column name storing the project ID for RBAC filtering, if applicable",
    )
    owner_email_column: str | None = Field(
        default=None,
        description="Column name storing the owner email for SELF-scope RBAC filtering, if applicable",
    )


# Authoritative configurations for enterprise dimension tables
DEFAULT_ENTITY_TABLE_CONFIGS: dict[str, EntityTableConfig] = {
    "projectname": EntityTableConfig(
        table_name="ProjectName",
        primary_key_column="id",
        searchable_columns=["id", "projectName", "verticalCode", "pricingModel"],
        label_template="{projectName} (ID: {id})",
        vertical_code_column="verticalCode",
        project_id_column="id",
    ),
    "vertical": EntityTableConfig(
        table_name="Vertical",
        primary_key_column="verticalCode",
        searchable_columns=["verticalCode", "verticalName", "area"],
        label_template="{verticalName} ({verticalCode})",
        vertical_code_column="verticalCode",
    ),
    "employeeinformation": EntityTableConfig(
        table_name="EmployeeInformation",
        primary_key_column="employeeMailId",
        searchable_columns=["employeeMailId", "employeeName", "designation", "verticalCode"],
        label_template="{employeeName} <{employeeMailId}>",
        vertical_code_column="verticalCode",
        owner_email_column="employeeMailId",
    ),
}


class EntityValueDocument(BaseModel):
    """
    Canonical document representing a specific database row entity for vector embedding.
    """

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(
        ...,
        description="Deterministic document identifier: '{database_id}:{schema_name}:{table_name}:{primary_key_value}:ENTITY'",
    )
    database_id: str = Field(default="default", description="Database identifier")
    schema_name: str = Field(default="public", description="PostgreSQL schema name")
    table_name: str = Field(..., description="Canonical table name")
    primary_key_column: str = Field(..., description="Name of the primary key column")
    primary_key_value: str = Field(..., description="String value of the primary key")
    entity_label: str = Field(..., description="Concise human-readable label for prompt injection")
    searchable_text: str = Field(..., description="Text embedded into vector space")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured RBAC metadata (vertical_code, project_id, owner_email, table_name)",
    )
    content_hash: str = Field(
        ...,
        description="SHA-256 hash of entity text for change detection",
    )

    @staticmethod
    def build_document_id(
        database_id: str,
        schema_name: str,
        table_name: str,
        primary_key_value: str,
    ) -> str:
        """
        Generate deterministic document ID for an entity row.
        """
        db = database_id.strip().lower()
        schema = schema_name.strip().lower()
        tbl = table_name.strip().lower()
        pk = primary_key_value.strip().lower()
        return f"{db}:{schema}:{tbl}:{pk}:ENTITY"

    @staticmethod
    def compute_content_hash(text: str, label: str = "") -> str:
        """
        Compute SHA-256 hash of searchable text and label.
        """
        raw = f"{text.strip()}::{label.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def create(
        cls,
        table_name: str,
        primary_key_column: str,
        primary_key_value: str,
        entity_label: str,
        searchable_text: str,
        database_id: str = "default",
        schema_name: str = "public",
        vertical_code: str | None = None,
        project_id: str | None = None,
        owner_email: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> "EntityValueDocument":
        """
        Factory to instantiate and validate an EntityValueDocument.
        """
        doc_id = cls.build_document_id(
            database_id=database_id,
            schema_name=schema_name,
            table_name=table_name,
            primary_key_value=primary_key_value,
        )
        content_hash = cls.compute_content_hash(searchable_text, label=entity_label)

        meta: dict[str, Any] = {
            "table_name": table_name.strip(),
            "primary_key_column": primary_key_column.strip(),
            "primary_key_value": primary_key_value.strip(),
            "entity_label": entity_label.strip(),
            "vertical_code": vertical_code.strip().upper() if vertical_code else None,
            "project_id": project_id.strip() if project_id else None,
            "owner_email": owner_email.strip().lower() if owner_email else None,
        }
        if extra_metadata:
            meta.update(extra_metadata)

        return cls(
            document_id=doc_id,
            database_id=database_id,
            schema_name=schema_name,
            table_name=table_name,
            primary_key_column=primary_key_column,
            primary_key_value=primary_key_value,
            entity_label=entity_label,
            searchable_text=searchable_text,
            metadata=meta,
            content_hash=content_hash,
        )


class EntityMatchResult(BaseModel):
    """
    Result returned when an entity embedding matches a user's question.
    """

    model_config = ConfigDict(frozen=True)

    table_name: str = Field(..., description="Target database table")
    primary_key_column: str = Field(..., description="Target primary key column")
    primary_key_value: str = Field(..., description="Exact primary key value to filter in SQL")
    entity_label: str = Field(..., description="Human-readable entity label")
    score: float = Field(..., description="Cosine similarity score")
    matched_text: str = Field(..., description="Searchable text of the matched entity")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
