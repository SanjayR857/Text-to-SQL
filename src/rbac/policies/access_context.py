"""
Access context and granular authorization models.

Defines table, column, operation-specific permissions, and resolved access
context for the enterprise Text-to-SQL authorization engine.
"""
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from rbac.policies.predicate_spec import PredicateSpec
from rbac.identity.user import UserContext


class AccessScope(str, Enum):
    """
    Access scope levels for data access governance.
    """

    ALL = "ALL"              # Full access across enterprise (Admin / EP)
    VERTICAL = "VERTICAL"    # Filtered by authorized vertical codes
    PROJECT = "PROJECT"      # Filtered by authorized project IDs
    PMO = "PMO"              # Filtered by staffed resources on user's PMO projects
    SELF = "SELF"            # Filtered by caller identity (e.g. employeeMailId)
    CUSTOM = "CUSTOM"        # Specialized domain policy logic
    NONE = "NONE"            # Default deny / unauthorized


class ColumnSensitivity(str, Enum):
    """
    Data sensitivity classification for database columns.
    """

    PUBLIC = "PUBLIC"              # Open internal reference (e.g., department names, lookup codes)
    INTERNAL = "INTERNAL"          # General internal operational data
    RESTRICTED = "RESTRICTED"      # Scoped business data (candidate CTC, project commercials)
    CONFIDENTIAL = "CONFIDENTIAL"  # Strictly protected PII / executive compensation


class ColumnPermission(BaseModel):
    """
    Operation-specific authorization permissions for a database column.

    Explicitly decouples SELECT, FILTER, JOIN, GROUP BY, and AGGREGATE
    capabilities to prevent unauthorized projection, filtering inference,
    or statistical probing attacks.
    """

    model_config = ConfigDict(frozen=True)

    column_name: str = Field(..., description="Target column name")
    sensitivity: ColumnSensitivity = Field(
        default=ColumnSensitivity.INTERNAL,
        description="Data sensitivity classification",
    )
    can_select: bool = Field(
        default=False,
        description="May appear in SELECT projection list or output",
    )
    can_filter: bool = Field(
        default=False,
        description="May appear in WHERE or HAVING filter clauses",
    )
    can_join: bool = Field(
        default=False,
        description="May appear in JOIN ON conditions",
    )
    can_group: bool = Field(
        default=False,
        description="May appear in GROUP BY clauses",
    )
    can_aggregate: bool = Field(
        default=False,
        description="May appear inside aggregate functions (COUNT, SUM, AVG, MIN, MAX)",
    )


class TablePermission(BaseModel):
    """
    Resolved permissions and row predicates for a specific database table.
    """

    model_config = ConfigDict(frozen=True)

    table_name: str = Field(..., description="Canonical table name")
    can_read: bool = Field(
        default=False,
        description="Whether user can query this table at all",
    )
    scope: AccessScope = Field(
        default=AccessScope.NONE,
        description="Row-level access scope",
    )
    columns: dict[str, ColumnPermission] = Field(
        default_factory=dict,
        description="Column-level permissions keyed by lowercase column name",
    )
    predicates: list[PredicateSpec] = Field(
        default_factory=list,
        description="List of row-filtering predicates to inject",
    )

    @property
    def allowed_select_columns(self) -> set[str]:
        """Set of lowercase column names permitted in SELECT projections."""
        return {name.lower() for name, p in self.columns.items() if p.can_select}

    @property
    def allowed_filter_columns(self) -> set[str]:
        """Set of lowercase column names permitted in WHERE/HAVING filters."""
        return {name.lower() for name, p in self.columns.items() if p.can_filter}

    @property
    def allowed_join_columns(self) -> set[str]:
        """Set of lowercase column names permitted in JOIN ON conditions."""
        return {name.lower() for name, p in self.columns.items() if p.can_join}

    @property
    def allowed_group_columns(self) -> set[str]:
        """Set of lowercase column names permitted in GROUP BY clauses."""
        return {name.lower() for name, p in self.columns.items() if p.can_group}

    @property
    def allowed_aggregate_columns(self) -> set[str]:
        """Set of lowercase column names permitted inside aggregate functions."""
        return {name.lower() for name, p in self.columns.items() if p.can_aggregate}

    def get_column_permission(self, column_name: str) -> ColumnPermission | None:
        """
        Look up column permission case-insensitively.

        Args:
            column_name: Name of column to check.

        Returns:
            ColumnPermission if registered, None otherwise.
        """
        return self.columns.get(column_name.lower())


class ResolvedAccessContext(BaseModel):
    """
    Complete resolved authorization context for a database query session.

    Contains verified user identity, effective table permissions, and parameter
    values bound securely for query execution.
    """

    model_config = ConfigDict(frozen=True)

    user_context: UserContext = Field(
        ...,
        description="Resolved user identity and assignment context",
    )
    table_permissions: dict[str, TablePermission] = Field(
        default_factory=dict,
        description="Table permissions keyed by lowercase table name",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Safe SQL query parameters to bind during execution",
    )

    @property
    def allowed_tables(self) -> set[str]:
        """Set of lowercase table names the user has permission to read."""
        return {name.lower() for name, p in self.table_permissions.items() if p.can_read}

    def is_table_accessible(self, table_name: str) -> bool:
        """
        Check if table is accessible for read queries.

        Args:
            table_name: Table name to check.

        Returns:
            True if table exists in permissions and can_read is True, False otherwise.
        """
        perm = self.table_permissions.get(table_name.lower())
        return perm is not None and perm.can_read

    def get_table_permission(self, table_name: str) -> TablePermission | None:
        """
        Retrieve table permission case-insensitively.

        Args:
            table_name: Table name to look up.

        Returns:
            TablePermission if present, None otherwise.
        """
        return self.table_permissions.get(table_name.lower())
