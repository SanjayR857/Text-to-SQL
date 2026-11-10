"""
Predicate specifications for row-level authorization.

Encapsulates typed AST predicate rules and parameter references without
raw SQL string concatenation or database-level RLS functions.
"""
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PredicateOperator(str, Enum):
    """
    Supported comparison operators for row-level predicate injection.
    """

    EQ = "EQ"                      # Column = :param
    IN = "IN"                      # Column IN (:param)
    IS_NOT_NULL = "IS_NOT_NULL"    # Column IS NOT NULL
    ALWAYS_FALSE = "ALWAYS_FALSE"  # 1 = 0 (Default deny)
    CUSTOM = "CUSTOM"              # Parameterized custom SQL expression template


class PredicateSpec(BaseModel):
    """
    Immutable specification of a row-level access predicate.

    Defines the target column, comparison operator, and the parameter name
    holding the verified value(s) in the query execution context.
    """

    model_config = ConfigDict(frozen=True)

    column: str = Field(
        ...,
        description="Target column name to apply predicate on (e.g., employeeMailId, verticalCode)",
    )
    operator: PredicateOperator = Field(
        ...,
        description="Comparison operator to evaluate",
    )
    parameter_name: str = Field(
        default="",
        description="Bound parameter name in the execution parameters dictionary",
    )
    cast_type: str | None = Field(
        default=None,
        description="Optional SQL type cast for parameter/column (e.g., UUID, VARCHAR)",
    )
    is_derived_subquery: bool = Field(
        default=False,
        description="Whether this predicate requires wrapping the target table in a derived subquery (e.g., for outer joins)",
    )
    derived_subquery_alias: str | None = Field(
        default=None,
        description="Optional alias to use when wrapping table in a derived subquery",
    )
    custom_expression: str | None = Field(
        default=None,
        description="Parameterized SQL template when operator is CUSTOM",
    )

    @model_validator(mode="after")
    def validate_predicate_config(self) -> "PredicateSpec":
        """
        Validate operator-specific constraints.

        Returns:
            Self if validation succeeds.

        Raises:
            ValueError: If required fields for an operator are missing or invalid.
        """
        if self.operator == PredicateOperator.CUSTOM and not self.custom_expression:
            raise ValueError("custom_expression must be provided when operator is CUSTOM")

        if self.operator not in (PredicateOperator.ALWAYS_FALSE, PredicateOperator.IS_NOT_NULL):
            if not self.parameter_name and self.operator != PredicateOperator.CUSTOM:
                raise ValueError(
                    f"parameter_name must be non-empty for operator '{self.operator.value}'"
                )

        return self

    @classmethod
    def for_self(
        cls,
        column: str = "employeeMailId",
        parameter_name: str = "auth_user_email",
    ) -> "PredicateSpec":
        """
        Create a SELF scope predicate matching caller identity.

        Args:
            column: Email column name on the target table (defaults to 'employeeMailId').
            parameter_name: Bound parameter holding the normalized email.

        Returns:
            PredicateSpec enforcing caller email equality.
        """
        return cls(
            column=column,
            operator=PredicateOperator.EQ,
            parameter_name=parameter_name,
        )

    @classmethod
    def for_vertical(
        cls,
        column: str = "verticalCode",
        parameter_name: str = "auth_vertical_codes",
    ) -> "PredicateSpec":
        """
        Create a VERTICAL scope predicate filtering by authorized vertical codes.

        Args:
            column: Vertical code column name (defaults to 'verticalCode').
            parameter_name: Bound parameter holding the list of vertical codes.

        Returns:
            PredicateSpec enforcing vertical membership.
        """
        return cls(
            column=column,
            operator=PredicateOperator.IN,
            parameter_name=parameter_name,
        )

    @classmethod
    def for_project(
        cls,
        column: str = "projectId",
        parameter_name: str = "auth_project_ids",
    ) -> "PredicateSpec":
        """
        Create a PROJECT scope predicate filtering by authorized project IDs.

        Args:
            column: Project identifier column name (defaults to 'projectId').
            parameter_name: Bound parameter holding the list of project IDs.

        Returns:
            PredicateSpec enforcing project membership.
        """
        return cls(
            column=column,
            operator=PredicateOperator.IN,
            parameter_name=parameter_name,
        )

    @classmethod
    def deny(cls, column: str = "id") -> "PredicateSpec":
        """
        Create a default-deny predicate that always evaluates to false.

        Args:
            column: Arbitrary column reference for AST representation.

        Returns:
            PredicateSpec that fails all rows (1 = 0).
        """
        return cls(
            column=column,
            operator=PredicateOperator.ALWAYS_FALSE,
            parameter_name="",
        )
