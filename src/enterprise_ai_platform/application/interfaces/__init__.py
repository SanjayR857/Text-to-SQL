"""
Application interface ports for LLM generation and vector embeddings.
"""
from enterprise_ai_platform.application.interfaces.embedding_provider import (
    EmbeddingProviderProtocol,
)
from enterprise_ai_platform.application.interfaces.llm_provider import (
    ChatMessage,
    LLMCompletionResponse,
    LLMProviderProtocol,
)

__all__ = [
    "ChatMessage",
    "LLMCompletionResponse",
    "LLMProviderProtocol",
    "EmbeddingProviderProtocol",
]
