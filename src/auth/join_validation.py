"""
Approved join graph registry and join validation engine.

Ensures all SQL table joins conform to predefined, enterprise-approved
relationships and eliminates cartesian products, cross-joins, and join-bypass attacks.
"""
from typing import Set

from pydantic import BaseModel, ConfigDict, Field
from sqlglot import exp

from auth.access_context import (
    ResolvedAccessContext,
)
from core.exceptions import JoinAccessDeniedError


class ApprovedJoinEdge(BaseModel):
    """
    Specification of an approved join relationship between two database tables.
    """

    model_config = ConfigDict(frozen=True)

    source_table: str = Field(..., description="Source table name")
    source_column: str = Field(..., description="Source table join column")
    target_table: str = Field(..., description="Target table name")
    target_column: str = Field(..., description="Target table join column")
    relationship: str = Field(default="ONE_TO_MANY", description="Relationship cardinality")
    description: str = Field(default="", description="Semantic description of the relationship")

    def matches(self, table_a: str, col_a: str, table_b: str, col_b: str) -> bool:
        """
        Check if given table-column pairs match this edge symmetrically.

        Args:
            table_a: First table name.
            col_a: First column name.
            table_b: Second table name.
            col_b: Second column name.

        Returns:
            True if (table_a.col_a, table_b.col_b) matches this edge in either direction.
        """
        ta, ca = table_a.strip().lower(), col_a.strip().lower()
        tb, cb = table_b.strip().lower(), col_b.strip().lower()
        src_t, src_c = self.source_table.lower(), self.source_column.lower()
        tgt_t, tgt_c = self.target_table.lower(), self.target_column.lower()

        # Forward match
        if ta == src_t and ca == src_c and tb == tgt_t and cb == tgt_c:
            return True
        # Symmetric reverse match
        if ta == tgt_t and ca == tgt_c and tb == src_t and cb == src_c:
            return True

        return False


# Canonical enterprise join graph covering the platform's 13 business modules
ENTERPRISE_APPROVED_JOINS: list[ApprovedJoinEdge] = [
    # Module 3: Projects, Allocations & Commercials
    ApprovedJoinEdge(
        source_table="ProjectName",
        source_column="id",
        target_table="ProjectDetail",
        target_column="projectId",
        relationship="ONE_TO_MANY",
        description="Project master to staffing resource allocations",
    ),
    ApprovedJoinEdge(
        source_table="ProjectName",
        source_column="id",
        target_table="Contract",
        target_column="projectId",
        relationship="ONE_TO_MANY",
        description="Project master to commercial contracts",
    ),
    ApprovedJoinEdge(
        source_table="ProjectName",
        source_column="id",
        target_table="Milestone",
        target_column="projectId",
        relationship="ONE_TO_MANY",
        description="Project master to deliverable billing milestones",
    ),
    ApprovedJoinEdge(
        source_table="ProjectName",
        source_column="id",
        target_table="ContractAmendment",
        target_column="projectId",
        relationship="ONE_TO_MANY",
        description="Project master to SOW contract amendments",
    ),
    ApprovedJoinEdge(
        source_table="ProjectName",
        source_column="id",
        target_table="Demand",
        target_column="projectId",
        relationship="ONE_TO_MANY",
        description="Project master to hiring demand requisitions",
    ),
    ApprovedJoinEdge(
        source_table="ProjectName",
        source_column="id",
        target_table="KpiGoal",
        target_column="projectId",
        relationship="ONE_TO_MANY",
        description="Project master to deliverable KPI goals",
    ),
    ApprovedJoinEdge(
        source_table="ProjectName",
        source_column="id",
        target_table="EmployeeGoalAssignment",
        target_column="projectId",
        relationship="ONE_TO_MANY",
        description="Project master to employee goal assignments",
    ),
    ApprovedJoinEdge(
        source_table="ProjectName",
        source_column="id",
        target_table="QuarterlyRating",
        target_column="projectId",
        relationship="ONE_TO_MANY",
        description="Project master to delivery quarterly ratings",
    ),
    # Module 2 & 9: Employee Directory, Attendance & Allocations
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="OfficeAttendance",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to daily badge-swipe attendance",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="FirmContribution",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to firm contributions and initiatives",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="ProjectDetail",
        target_column="resourceMailID",
        relationship="ONE_TO_MANY",
        description="Employee profile to staffed project details",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="EmployeeChiefAreaSelection",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to chief vertical area selections",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="ChiefGoalRating",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to chief goal evaluation ratings",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="EmployeeGoalAssignment",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to project goal assignments",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="QuarterlyRating",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to quarterly delivery scores",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="Recognition",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to peer and leadership recognitions",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="BadgeOfHonorAward",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to badge of honor conferrals",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="QuarterExclusion",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to appraisal exclusion records",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="EmployeeTalentGPSInfo",
        target_column="employeeMailId",
        relationship="ONE_TO_MANY",
        description="Employee profile to talent GPS skills inventory",
    ),
    ApprovedJoinEdge(
        source_table="EmployeeInformation",
        source_column="employeeMailId",
        target_table="RatingComment",
        target_column="rateeEmail",
        relationship="ONE_TO_MANY",
        description="Employee profile to qualitative rating comments",
    ),
    # Module 10: Demand & Talent Sourcing
    ApprovedJoinEdge(
        source_table="Demand",
        source_column="id",
        target_table="DemandCandidate",
        target_column="demandId",
        relationship="ONE_TO_MANY",
        description="Demand requisition to candidate pipeline",
    ),
    ApprovedJoinEdge(
        source_table="Demand",
        source_column="id",
        target_table="PanelInfo",
        target_column="demandId",
        relationship="ONE_TO_MANY",
        description="Demand requisition to interview panels",
    ),
    ApprovedJoinEdge(
        source_table="Demand",
        source_column="id",
        target_table="DemandSourcingRound",
        target_column="demandId",
        relationship="ONE_TO_MANY",
        description="Demand requisition to sourcing rounds",
    ),
    ApprovedJoinEdge(
        source_table="Demand",
        source_column="id",
        target_table="DemandEvent",
        target_column="demandId",
        relationship="ONE_TO_MANY",
        description="Demand requisition to event timeline",
    ),
    # Module 6, 7 & 8: Goals & Evaluation Links
    ApprovedJoinEdge(
        source_table="ChiefGoal",
        source_column="id",
        target_table="ChiefGoalRating",
        target_column="goalId",
        relationship="ONE_TO_MANY",
        description="Chief goal definition to ratings",
    ),
    ApprovedJoinEdge(
        source_table="PartnerGoal",
        source_column="id",
        target_table="PartnerGoalRating",
        target_column="goalId",
        relationship="ONE_TO_MANY",
        description="Partner goal definition to chief ratings",
    ),
    ApprovedJoinEdge(
        source_table="PartnerGoal",
        source_column="id",
        target_table="PartnerGoalMessage",
        target_column="goalId",
        relationship="ONE_TO_MANY",
        description="Partner goal definition to discussion messages",
    ),
    ApprovedJoinEdge(
        source_table="EmGoal",
        source_column="id",
        target_table="EmGoalRating",
        target_column="goalId",
        relationship="ONE_TO_MANY",
        description="EM goal definition to ratings",
    ),
    ApprovedJoinEdge(
        source_table="EmGoal",
        source_column="id",
        target_table="EmGoalMessage",
        target_column="goalId",
        relationship="ONE_TO_MANY",
        description="EM goal definition to messages",
    ),
    ApprovedJoinEdge(
        source_table="KpiGoal",
        source_column="id",
        target_table="KpiGoalRole",
        target_column="goalId",
        relationship="ONE_TO_MANY",
        description="KPI goal to role mappings",
    ),
    ApprovedJoinEdge(
        source_table="KpiGoal",
        source_column="id",
        target_table="QuarterlyRating",
        target_column="goalId",
        relationship="ONE_TO_MANY",
        description="KPI goal to quarterly evaluations",
    ),
    # Module 1: Vertical References
    ApprovedJoinEdge(
        source_table="Vertical",
        source_column="code",
        target_table="ChiefGoal",
        target_column="verticalCode",
        relationship="ONE_TO_MANY",
        description="Vertical master to chief goals",
    ),
    ApprovedJoinEdge(
        source_table="Vertical",
        source_column="code",
        target_table="PartnerGoal",
        target_column="verticalCode",
        relationship="ONE_TO_MANY",
        description="Vertical master to partner goals",
    ),
    ApprovedJoinEdge(
        source_table="Vertical",
        source_column="code",
        target_table="EmGoal",
        target_column="verticalCode",
        relationship="ONE_TO_MANY",
        description="Vertical master to EM goals",
    ),
    ApprovedJoinEdge(
        source_table="Vertical",
        source_column="code",
        target_table="RoleAssignment",
        target_column="verticalCode",
        relationship="ONE_TO_MANY",
        description="Vertical master to user role bindings",
    ),
    ApprovedJoinEdge(
        source_table="Vertical",
        source_column="code",
        target_table="EmployeeChiefAreaSelection",
        target_column="verticalCode",
        relationship="ONE_TO_MANY",
        description="Vertical master to employee chief selections",
    ),
]


class JoinGraphValidator:
    """
    Validates all JOIN relationships in a SQLGlot AST against approved enterprise edges.
    """

    def __init__(self, approved_joins: list[ApprovedJoinEdge] | None = None) -> None:
        """
        Initialize validator with approved join edges.

        Args:
            approved_joins: Optional list of approved edges (defaults to ENTERPRISE_APPROVED_JOINS).
        """
        self._edges: list[ApprovedJoinEdge] = approved_joins or ENTERPRISE_APPROVED_JOINS

    def is_join_approved(self, table_a: str, col_a: str, table_b: str, col_b: str) -> bool:
        """
        Check if join between table_a.col_a and table_b.col_b is approved.

        Args:
            table_a: First table name.
            col_a: First column name.
            table_b: Second table name.
            col_b: Second column name.

        Returns:
            True if edge exists in approved graph, False otherwise.
        """
        return any(edge.matches(table_a, col_a, table_b, col_b) for edge in self._edges)

    def get_approved_joins_for_tables(self, allowed_tables: Set[str]) -> list[ApprovedJoinEdge]:
        """
        Retrieve approved edges where both endpoints are in the allowed tables set.

        Used to dynamically inject prompt join hints during schema retrieval.

        Args:
            allowed_tables: Set of accessible table names (case-insensitive).

        Returns:
            List of approved join edges between the accessible tables.
        """
        clean_tables = {t.lower() for t in allowed_tables}
        return [
            edge
            for edge in self._edges
            if edge.source_table.lower() in clean_tables
            and edge.target_table.lower() in clean_tables
        ]

    def format_join_hints_for_prompt(self, allowed_tables: Set[str]) -> str:
        """
        Format approved join relationships into prompt instructions for the LLM.

        Args:
            allowed_tables: Set of accessible tables.

        Returns:
            Formatted join instructions markdown snippet.
        """
        edges = self.get_approved_joins_for_tables(allowed_tables)
        if not edges:
            return ""

        lines = ["### Approved Table Join Relationships (Use ONLY these joins):"]
        for e in edges:
            lines.append(
                f"- `{e.source_table}.{e.source_column} = {e.target_table}.{e.target_column}`: {e.description}"
            )
        return "\n".join(lines)

    def validate_joins(self, ast: exp.Expression, access_context: ResolvedAccessContext) -> None:
        """
        Inspect all JOIN and FROM nodes in the AST and reject unauthorized joins.

        Enforces:
            1. No cross joins or cartesian products.
            2. JOIN ON conditions must not contain OR disjunctions (blocks OR 1=1).
            3. Every join equality condition must match an approved edge in the join graph.
            4. Both endpoints must have can_join = True in TablePermission.
            5. Both endpoints must be in access_context.allowed_tables.

        Args:
            ast: Parsed SQLGlot AST expression.
            access_context: Resolved caller access context.

        Raises:
            JoinAccessDeniedError: If any unapproved join, cartesian product, or bypass is detected.
        """
        # Resolve alias map in the query: alias -> physical_table
        alias_map = self._build_alias_map(ast)

        # 1. Check for comma-separated Cartesian products: SELECT * FROM A, B
        for select in ast.find_all(exp.Select):
            from_clause = select.args.get("from")
            if from_clause:
                # Multiple tables in FROM without explicit JOIN
                expressions = from_clause.expressions
                if len(expressions) > 1:
                    raise JoinAccessDeniedError(
                        "Implicit comma joins (Cartesian products) are forbidden. Use explicit INNER/LEFT JOIN."
                    )

        # 2. Inspect all explicit JOIN nodes
        for join in ast.find_all(exp.Join):
            # Check for CROSS JOIN
            if join.kind and "CROSS" in join.kind.upper():
                raise JoinAccessDeniedError("CROSS JOIN operations are strictly forbidden.")

            on_clause = join.args.get("on")
            if on_clause is None:
                raise JoinAccessDeniedError(
                    "Join missing ON condition. Cartesian products are forbidden."
                )

            # Check for disjunctions (OR 1=1 bypass)
            if list(on_clause.find_all(exp.Or)):
                raise JoinAccessDeniedError(
                    "OR disjunctions inside JOIN ON clauses are forbidden to prevent join bypass attacks."
                )

            # Decompose conjunctions: ON a.x = b.y AND a.z = b.w
            equalities = list(on_clause.find_all(exp.EQ))
            if not equalities:
                raise JoinAccessDeniedError(
                    "JOIN ON condition must specify at least one equality expression."
                )

            for eq in equalities:
                left = eq.this
                right = eq.expression

                if not isinstance(left, exp.Column) or not isinstance(right, exp.Column):
                    raise JoinAccessDeniedError(
                        "JOIN condition must compare direct table columns (literal tautologies forbidden)."
                    )

                left_table = self._resolve_table(left, alias_map)
                right_table = self._resolve_table(right, alias_map)
                left_col = left.name
                right_col = right.name

                # Validate join endpoints are in allowed tables
                if not access_context.is_table_accessible(left_table):
                    raise JoinAccessDeniedError(
                        f"Join references inaccessible table '{left_table}'."
                    )
                if not access_context.is_table_accessible(right_table):
                    raise JoinAccessDeniedError(
                        f"Join references inaccessible table '{right_table}'."
                    )

                # Validate can_join permission on both columns
                left_perm = access_context.get_table_permission(left_table)
                right_perm = access_context.get_table_permission(right_table)

                if left_perm and left_col.lower() not in left_perm.allowed_join_columns:
                    raise JoinAccessDeniedError(
                        f"Column '{left_table}.{left_col}' is not authorized for JOIN operations."
                    )
                if right_perm and right_col.lower() not in right_perm.allowed_join_columns:
                    raise JoinAccessDeniedError(
                        f"Column '{right_table}.{right_col}' is not authorized for JOIN operations."
                    )

                # Validate against Approved Join Graph
                if not self.is_join_approved(left_table, left_col, right_table, right_col):
                    raise JoinAccessDeniedError(
                        f"Join between '{left_table}.{left_col}' and '{right_table}.{right_col}' is not approved."
                    )

    def _build_alias_map(self, ast: exp.Expression) -> dict[str, str]:
        """Build a mapping of table aliases to physical table names."""
        aliases: dict[str, str] = {}
        for table in ast.find_all(exp.Table):
            table_name = table.name
            alias = table.alias_or_name
            aliases[alias.lower()] = table_name
            aliases[table_name.lower()] = table_name
        return aliases

    def _resolve_table(self, col: exp.Column, alias_map: dict[str, str]) -> str:
        """Resolve the physical table name for a column reference."""
        table_ref = col.table
        if not table_ref:
            raise JoinAccessDeniedError(
                f"Unqualified column reference '{col.name}' inside JOIN condition is ambiguous."
            )
        resolved = alias_map.get(table_ref.lower())
        if not resolved:
            return table_ref
        return resolved
