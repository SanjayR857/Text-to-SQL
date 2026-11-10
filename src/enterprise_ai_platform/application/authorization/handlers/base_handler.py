"""
Abstract base policy handler contract.
"""
from abc import ABC, abstractmethod
from typing import Any

from enterprise_ai_platform.application.authorization.access_context import (
    ColumnPermission,
    ColumnSensitivity,
    TablePermission,
)
from enterprise_ai_platform.domain.identity.user import UserContext


class BasePolicyHandler(ABC):
    """
    Abstract contract for resolving access permissions and row predicates on database tables.
    """

    @abstractmethod
    def can_handle(self, table_name: str) -> bool:
        """
        Check if this handler manages policy evaluation for the given table.

        Args:
            table_name: Canonical table name to check.

        Returns:
            True if this handler is responsible for the table, False otherwise.
        """
        ...

    @abstractmethod
    def resolve_table_permission(
        self,
        table_name: str,
        user_context: UserContext,
        parameters: dict[str, Any],
    ) -> TablePermission:
        """
        Resolve effective TablePermission and register bound parameters.

        Args:
            table_name: Canonical table name to evaluate.
            user_context: Authenticated caller identity and role context.
            parameters: Mutable dictionary to bind query execution parameters.

        Returns:
            Resolved TablePermission.
        """
        ...

    @staticmethod
    def _col(
        name: str,
        sensitivity: ColumnSensitivity = ColumnSensitivity.INTERNAL,
        can_select: bool = True,
        can_filter: bool = True,
        can_join: bool = True,
        can_group: bool = True,
        can_aggregate: bool = True,
    ) -> ColumnPermission:
        """
        Helper utility to instantiate a ColumnPermission with operation flags.

        Args:
            name: Column name.
            sensitivity: Sensitivity tier.
            can_select: Selectability flag.
            can_filter: Filterability flag.
            can_join: Joinability flag.
            can_group: Groupability flag.
            can_aggregate: Aggregatability flag.

        Returns:
            Configured ColumnPermission instance.
        """
        return ColumnPermission(
            column_name=name,
            sensitivity=sensitivity,
            can_select=can_select,
            can_filter=can_filter,
            can_join=can_join,
            can_group=can_group,
            can_aggregate=can_aggregate,
        )
