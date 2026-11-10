"""
Authorized schema projection and prompt hint service.

Projects authorized database schemas and approved join relationships for Text-to-SQL
prompt generation, completely hiding unauthorized tables and sensitive columns.
"""
from typing import Set

from rbac.access_context import (
    ResolvedAccessContext,
    TablePermission,
)
from rbac.join_validation import (
    JoinGraphValidator,
)


class AuthorizedSchemaService:
    """
    Constructs authorized schema representations and join hints for LLM prompts.
    """

    def __init__(self, join_validator: JoinGraphValidator | None = None) -> None:
        """
        Initialize schema service with join graph validator.

        Args:
            join_validator: Optional JoinGraphValidator instance.
        """
        self._join_validator = join_validator or JoinGraphValidator()

    def get_authorized_table_catalog(
        self,
        access_context: ResolvedAccessContext,
    ) -> dict[str, list[str]]:
        """
        Extract catalog of accessible tables and permitted selectable columns.

        Args:
            access_context: Resolved caller access context.

        Returns:
            Dictionary mapping canonical table names to sorted lists of selectable column names.
        """
        catalog: dict[str, list[str]] = {}

        for tbl_name in access_context.allowed_tables:
            perm = access_context.get_table_permission(tbl_name)
            if perm and perm.can_read:
                # Retrieve original column casing from ColumnPermission objects where can_select=True
                cols = [
                    p.column_name
                    for p in perm.columns.values()
                    if p.can_select
                ]
                catalog[perm.table_name] = sorted(cols)

        return catalog

    def build_prompt_schema(
        self,
        access_context: ResolvedAccessContext,
        target_tables: list[str] | None = None,
    ) -> str:
        """
        Build a markdown-formatted schema context for inclusion in the LLM prompt.

        Enforces:
            1. Tables with can_read=False are completely excluded.
            2. Columns with can_select=False are completely excluded.
            3. Approved join hints are included only for mutually accessible tables.

        Args:
            access_context: Resolved caller access context.
            target_tables: Optional list of relevant tables retrieved for the query.
                           If omitted, projects all accessible tables.

        Returns:
            Formatted markdown string ready for LLM prompt ingestion.
        """
        catalog = self.get_authorized_table_catalog(access_context)
        if not catalog:
            return "No accessible tables available for your active role."

        # Filter to target_tables if specified
        active_tables: dict[str, list[str]] = {}
        if target_tables is not None:
            clean_targets = {t.strip().lower() for t in target_tables}
            for tbl, cols in catalog.items():
                if tbl.lower() in clean_targets:
                    active_tables[tbl] = cols
        else:
            active_tables = catalog

        if not active_tables:
            return "No matching accessible tables available for your query."

        # Format schema tables
        lines: list[str] = [
            "### Authorized Database Schema",
            "You are authorized to query ONLY the following tables and columns:",
            "",
        ]

        for tbl_name in sorted(active_tables.keys()):
            cols = active_tables[tbl_name]
            lines.append(f"#### Table: `{tbl_name}`")
            lines.append("Columns:")
            for col in cols:
                lines.append(f"- `{col}`")
            lines.append("")

        # Append approved join relationships
        allowed_set: Set[str] = set(active_tables.keys())
        join_hints = self._join_validator.format_join_hints_for_prompt(allowed_set)
        if join_hints:
            lines.append(join_hints)
            lines.append("")

        # Append execution guidelines
        lines.extend([
            "### Query Execution Rules:",
            "1. Generate a single PostgreSQL SELECT query.",
            "2. Do NOT reference tables or columns not listed above.",
            "3. Use ONLY the approved join relationships listed above.",
            "4. Never use CROSS JOIN, multiple comma tables in FROM, or OR 1=1 in joins.",
        ])

        return "\n".join(lines)
