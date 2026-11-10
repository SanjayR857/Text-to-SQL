"""
Abstract checkpoint store port.

Defines the contract for persisting and retrieving multi-agent LangGraph workflow states.
"""
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class CheckpointRecord(BaseModel):
    """Normalized checkpoint state record."""

    model_config = ConfigDict(frozen=True)

    thread_id: str
    checkpoint_id: str
    parent_id: str | None = None
    state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CheckpointStoreProtocol(Protocol):
    """Protocol for saving and retrieving graph workflow execution checkpoints."""

    async def get_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str | None = None,
    ) -> CheckpointRecord | None:
        """Fetch the latest or specified checkpoint state for an execution thread."""
        ...

    async def save_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str,
        state: dict[str, Any],
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist a new checkpoint snapshot for a workflow thread."""
        ...
