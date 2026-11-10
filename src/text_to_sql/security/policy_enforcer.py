"""
Unified SQL policy enforcement engine.

Orchestrates AST syntax validation, join graph verification, scope resolution,
wildcard expansion, and row predicate injection.
"""
from typing import Any

from rbac.policies import (
    ResolvedAccessContext,
)
from rbac.validation import (
    JoinGraphValidator,
)
from text_to_sql.security.predicate_injector import (
    RowPredicateInjector,
)
from text_to_sql.security.ast_validator import (
    SqlAstValidator,
)
from text_to_sql.security.scope_resolver import (
    SqlScopeResolver,
)


class SqlPolicyEnforcer:
    """
    Coordinates end-to-end authorization enforcement on Text-to-SQL queries.
    """

    def __init__(
        self,
        ast_validator: SqlAstValidator | None = None,
        join_validator: JoinGraphValidator | None = None,
        scope_resolver: SqlScopeResolver | None = None,
        predicate_injector: RowPredicateInjector | None = None,
    ) -> None:
        """
        Initialize policy enforcer with security engine components.
        """
        self._ast_validator = ast_validator or SqlAstValidator()
        self._join_validator = join_validator or JoinGraphValidator()
        self._scope_resolver = scope_resolver or SqlScopeResolver()
        self._predicate_injector = predicate_injector or RowPredicateInjector()

    def enforce_policy(
        self,
        raw_sql: str,
        access_context: ResolvedAccessContext,
    ) -> tuple[str, dict[str, Any]]:
        """
        Validate, rewrite, and secure raw SQL against the caller's access context.

        Pipeline:
            1. Validate SQL syntax, single-statement constraint, analytical functions (SqlAstValidator).
            2. Validate JOIN operations against Approved Join Graph (JoinGraphValidator).
            3. Validate physical tables, expand wildcards, check column operation flags (SqlScopeResolver).
            4. Inject row-level scoping predicates and outer-join derived subqueries (RowPredicateInjector).
            5. Re-validate final AST structure (SqlAstValidator).
            6. Emit sanitized SQL and return alongside bound execution parameters.

        Args:
            raw_sql: Untrusted SQL string from LLM.
            access_context: Verified caller authorization context.

        Returns:
            Tuple of (enforced_sql_string, bound_parameters_dictionary).
        """
        # 1. Parse and validate syntax & AST security
        ast = self._ast_validator.validate_sql(raw_sql)

        # 2. Validate joins against Approved Join Graph
        self._join_validator.validate_joins(ast, access_context)

        # 3. Resolve scopes, expand wildcards, check column operation flags
        ast = self._scope_resolver.resolve_and_validate(ast, access_context)

        # 4. Inject scope-aware row predicates
        ast = self._predicate_injector.inject_predicates(ast, access_context)

        # 5. Revalidate transformed AST
        self._ast_validator.validate_ast(ast)

        # 6. Generate final SQL string
        enforced_sql = ast.sql()

        return enforced_sql, access_context.parameters
