"""
State schemas for LangGraph workflows (Chat, SQL, and Document RAG).
"""
from typing import Annotated, Any, Sequence
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


class AgentState(BaseModel):
    """Base state schema for multi-agent graph workflows."""
    messages: Sequence[BaseMessage] = Field(default_factory=list)
    user_context: dict[str, Any] = Field(default_factory=dict)
