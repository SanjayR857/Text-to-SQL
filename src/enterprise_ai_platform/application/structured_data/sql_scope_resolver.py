"""
SQL scope resolution, wildcard expansion, and operation-specific column authorization.
"""
from typing import Set

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import Scope, traverse_scope

from enterprise_ai_platform.application.authorization.access_context import (
    ResolvedAccessContext,
    TablePermission,
)
from enterprise_ai_platform.core.exceptions import (
    ColumnAccessDeniedError,
    TableAccessDeniedError,
)


class SqlScopeResolver:
    """
    Resolves AST scopes, expands wildcards, and enforces operation-specific column permissions.
    """

    def resolve_and_validate(
        self,
        ast: exp.Expression,
        access_context: ResolvedAccessContext,
    ) -> exp.Expression:
        """
        Validate table permissions, expand wildcards, and verify column operation flags.

        Steps:
            1. Validate physical table accessibility against access_context.allowed_tables.
            2. Expand SELECT * wildcards into explicit authorized columns.
            3. Validate projection columns against can_select.
            4. Validate filter clauses (WHERE, HAVING) against can_filter.
            5. Validate GROUP BY expressions against can_group.
            6. Validate all aggregate functions against can_aggregate.

        Args:
            ast: SQLGlot AST expression.
            access_context: Resolved caller access context.

        Returns:
            Rewritten AST with explicit column expansions.

        Raises:
            TableAccessDeniedError: If any unpermitted table is referenced.
            ColumnAccessDeniedError: If any unauthorized column operation is attempted.
        """
        # 1. Validate physical table accessibility
        self._validate_tables(ast, access_context)

        # 2. Expand wildcards (SELECT *) into explicit allowed_select_columns
        self._expand_wildcards(ast, access_context)

        # 3. Validate column operations across all scopes
        self._validate_column_operations(ast, access_context)

        return ast

    def _validate_tables(
        self,
        ast: exp.Expression,
        access_context: ResolvedAccessContext,
    ) -> None:
        """Verify that every physical table referenced in the query is accessible."""
        cte_names = {cte.alias_or_name.lower() for cte in ast.find_all(exp.CTE)}

        for table in ast.find_all(exp.Table):
            table_name = table.name
            if table_name.lower() in cte_names:
                continue

            if not access_context.is_table_accessible(table_name):
                raise TableAccessDeniedError(
                    f"Access Denied: Table '{table_name}' is not permitted for your active role."
                )

    def _expand_wildcards(
        self,
        ast: exp.Expression,
        access_context: ResolvedAccessContext,
    ) -> None:
        """Expand SELECT * expressions into explicit permitted columns."""
        cte_names = {cte.alias_or_name.lower() for cte in ast.find_all(exp.CTE)}

        for select in ast.find_all(exp.Select):
            has_star = any(isinstance(e, exp.Star) for e in select.expressions)
            if not has_star:
                continue

            # Identify primary table and alias in this select's FROM clause
            from_clause = select.find(exp.From)
            if not from_clause or not from_clause.this:
                continue

            from_table = from_clause.this
            if not isinstance(from_table, exp.Table):
                continue

            table_name = from_table.name
            if table_name.lower() in cte_names:
                continue

            alias = from_table.alias_or_name
            table_perm = access_context.get_table_permission(table_name)

            if not table_perm or not table_perm.allowed_select_columns:
                raise ColumnAccessDeniedError(
                    f"No selectable columns permitted on table '{table_name}'."
                )

            # Sort columns for deterministic output
            allowed_cols = sorted(table_perm.allowed_select_columns)

            new_expressions: list[exp.Expression] = []
            for expr in select.expressions:
                if isinstance(expr, exp.Star):
                    for col_name in allowed_cols:
                        new_expressions.append(exp.column(col_name, table=alias))
                else:
                    new_expressions.append(expr)

            select.set("expressions", new_expressions)

    def _validate_column_operations(
        self,
        ast: exp.Expression,
        access_context: ResolvedAccessContext,
    ) -> None:
        """
        Validate that every column reference complies with operation-specific flags.
        """
        alias_map = self._build_alias_map(ast)

        for select in ast.find_all(exp.Select):
            # 1. Validate SELECT projections (can_select)
            for expr in select.expressions:
                # Do not check columns that are wrapped in aggregate functions here
                # (they are checked in the aggregate step)
                if not isinstance(expr, exp.AggFunc):
                    for col in expr.find_all(exp.Column):
                        table = self._resolve_table(col, alias_map)
                        perm = access_context.get_table_permission(table)
                        if perm and col.name.lower() not in perm.allowed_select_columns:
                            raise ColumnAccessDeniedError(
                                f"Column '{table}.{col.name}' is sensitive and cannot be projected (can_select=False)."
                            )

            # 2. Validate Filter clauses: WHERE and HAVING (can_filter)
            where_clause = select.args.get("where")
            if where_clause:
                for col in where_clause.find_all(exp.Column):
                    table = self._resolve_table(col, alias_map)
                    perm = access_context.get_table_permission(table)
                    if perm and col.name.lower() not in perm.allowed_filter_columns:
                        raise ColumnAccessDeniedError(
                            f"Column '{table}.{col.name}' is sensitive and cannot be filtered (can_filter=False)."
                        )

            having_clause = select.args.get("having")
            if having_clause:
                for col in having_clause.find_all(exp.Column):
                    table = self._resolve_table(col, alias_map)
                    perm = access_context.get_table_permission(table)
                    if perm and col.name.lower() not in perm.allowed_filter_columns:
                        raise ColumnAccessDeniedError(
                            f"Column '{table}.{col.name}' is sensitive and cannot be filtered in HAVING (can_filter=False)."
                        )

            # 3. Validate GROUP BY expressions (can_group)
            group_clause = select.args.get("group")
            if group_clause:
                for col in group_clause.find_all(exp.Column):
                    table = self._resolve_table(col, alias_map)
                    perm = access_context.get_table_permission(table)
                    if perm and col.name.lower() not in perm.allowed_group_columns:
                        raise ColumnAccessDeniedError(
                            f"Column '{table}.{col.name}' is sensitive and cannot be grouped (can_group=False)."
                        )

            # 4. Validate Aggregate functions: COUNT, SUM, AVG, MIN, MAX (can_aggregate)
            for agg in select.find_all(exp.AggFunc):
                for col in agg.find_all(exp.Column):
                    table = self._resolve_table(col, alias_map)
                    perm = access_context.get_table_permission(table)
                    if perm and col.name.lower() not in perm.allowed_aggregate_columns:
                        raise ColumnAccessDeniedError(
                            f"Column '{table}.{col.name}' is sensitive and cannot be aggregated (can_aggregate=False)."
                        )

    def _build_alias_map(self, ast: exp.Expression) -> dict[str, str]:
        """Build table alias mapping for column resolution."""
        aliases: dict[str, str] = {}
        for table in ast.find_all(exp.Table):
            table_name = table.name
            alias = table.alias_or_name
            aliases[alias.lower()] = table_name
            aliases[table_name.lower()] = table_name
        return aliases

    def _resolve_table(self, col: exp.Column, alias_map: dict[str, str]) -> str:
        """Resolve physical table name for a column reference."""
        table_ref = col.table
        if table_ref:
            return alias_map.get(table_ref.lower(), table_ref)

        # If unqualified and only one physical table exists in alias_map
        distinct_tables = set(alias_map.values())
        if len(distinct_tables) == 1:
            return next(iter(distinct_tables))

        return ""
