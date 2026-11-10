"""
Row predicate injection engine.

Injects parameter-bound access predicates into SQL ASTs, preserving outer join
semantics via prefiltered derived subqueries and securing CTEs and subqueries.
"""
from typing import Set

import sqlglot
from sqlglot import exp

from rbac.access_context import (
    AccessScope,
    ResolvedAccessContext,
    TablePermission,
)
from rbac.predicate_spec import (
    PredicateOperator,
    PredicateSpec,
)


class RowPredicateInjector:
    """
    Transforms SQLGlot AST by injecting row-level scoping predicates.
    """

    def inject_predicates(
        self,
        ast: exp.Expression,
        access_context: ResolvedAccessContext,
    ) -> exp.Expression:
        """
        Inject parameter-bound row access predicates into the query AST.

        Handles:
            1. Outer Joins (LEFT/RIGHT JOIN): Rewrites target tables into prefiltered
               derived subqueries to preserve outer join semantics without dropping left rows.
            2. Direct Queries and Inner Joins: Injects predicates into the enclosing
               SELECT node's WHERE clause using AND.
            3. CTEs and Nested Subqueries: Recursively injects predicates at the physical
               table definition level.

        Args:
            ast: SQLGlot AST expression.
            access_context: Resolved caller access context containing table permissions.

        Returns:
            Rewritten AST with row predicates applied.
        """
        # Track tables handled via derived subquery rewriting so they aren't double-injected
        handled_table_ids: Set[int] = set()

        # Step 1: Handle Outer Joins (LEFT / RIGHT JOIN)
        self._rewrite_outer_joins(ast, access_context, handled_table_ids)

        # Step 2: Handle Direct Queries, CTEs, and Inner Joins
        self._inject_where_predicates(ast, access_context, handled_table_ids)

        return ast

    def _rewrite_outer_joins(
        self,
        ast: exp.Expression,
        access_context: ResolvedAccessContext,
        handled_table_ids: Set[int],
    ) -> None:
        """
        Rewrite outer join targets into prefiltered derived subqueries.

        Preserves outer join semantics so that left/right unmatched rows are not eliminated.
        """
        for join in ast.find_all(exp.Join):
            side = (join.side or "").upper()
            if side not in ("LEFT", "RIGHT"):
                continue

            target = join.this
            if not isinstance(target, exp.Table):
                continue

            table_name = target.name
            alias = target.alias_or_name
            perm = access_context.get_table_permission(table_name)

            if not perm or not perm.predicates:
                continue

            # Build derived subquery: SELECT * FROM TableName WHERE ...
            subquery_ast = sqlglot.parse_one(f"SELECT * FROM {table_name}")
            for pred in perm.predicates:
                pred_node = self._build_predicate_expression(pred, table_name)
                self._append_to_where(subquery_ast, pred_node)

            # Replace join target with derived subquery aliased back to original alias
            join.set("this", subquery_ast.subquery(alias))
            handled_table_ids.add(id(target))

    def _inject_where_predicates(
        self,
        ast: exp.Expression,
        access_context: ResolvedAccessContext,
        handled_table_ids: Set[int],
    ) -> None:
        """
        Inject predicates into WHERE clauses of direct queries, CTEs, and inner joins.
        """
        cte_names = {cte.alias_or_name.lower() for cte in ast.find_all(exp.CTE)}

        for select in ast.find_all(exp.Select):
            # 1. Inspect FROM table
            from_clause = select.find(exp.From)
            if from_clause and isinstance(from_clause.this, exp.Table):
                from_table = from_clause.this
                if from_table.name.lower() not in cte_names and id(from_table) not in handled_table_ids:
                    self._apply_table_predicates(select, from_table, access_context)

            # 2. Inspect INNER JOIN tables in this select
            for join in select.find_all(exp.Join):
                side = (join.side or "").upper()
                if side in ("LEFT", "RIGHT"):
                    continue

                if isinstance(join.this, exp.Table):
                    join_table = join.this
                    if join_table.name.lower() not in cte_names and id(join_table) not in handled_table_ids:
                        self._apply_table_predicates(select, join_table, access_context)

    def _apply_table_predicates(
        self,
        select: exp.Select,
        table: exp.Table,
        access_context: ResolvedAccessContext,
    ) -> None:
        """Apply all predicates for a specific physical table to the SELECT node's WHERE clause."""
        table_name = table.name
        alias = table.alias_or_name
        perm = access_context.get_table_permission(table_name)

        if not perm or not perm.predicates:
            return

        for pred in perm.predicates:
            pred_node = self._build_predicate_expression(pred, alias)
            self._append_to_where(select, pred_node)

    def _build_predicate_expression(self, pred: PredicateSpec, alias_or_table: str) -> exp.Expression:
        """
        Construct a typed SQLGlot expression for a PredicateSpec.
        """
        col_expr = exp.column(pred.column, table=alias_or_table)

        if pred.operator == PredicateOperator.ALWAYS_FALSE:
            return exp.EQ(this=exp.Literal.number(1), expression=exp.Literal.number(0))

        if pred.operator == PredicateOperator.IS_NOT_NULL:
            return exp.Is(this=col_expr, expression=exp.Null())

        if pred.operator == PredicateOperator.EQ:
            param_var = exp.var(f":{pred.parameter_name}")
            return exp.EQ(this=col_expr, expression=param_var)

        if pred.operator == PredicateOperator.IN:
            param_var = exp.var(f":{pred.parameter_name}")
            return exp.In(this=col_expr, expressions=[param_var])

        if pred.operator == PredicateOperator.CUSTOM:
            if pred.custom_expression:
                rendered = pred.custom_expression.replace("{alias}", alias_or_table)
                return sqlglot.parse_one(rendered)

        return exp.EQ(this=exp.Literal.number(1), expression=exp.Literal.number(0))

    def _append_to_where(self, select: exp.Select, pred_node: exp.Expression) -> None:
        """Append a predicate node to a Select's WHERE clause using AND conjunction."""
        where = select.find(exp.Where)
        if where is not None and where.this is not None:
            select.set("where", exp.Where(this=exp.and_(where.this, pred_node)))
        else:
            select.set("where", exp.Where(this=pred_node))
