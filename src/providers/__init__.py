"""
External AI model and embedding providers (Azure OpenAI, embeddings).
"""
from providers.azure_openai_client import (
    close_azure_openai_client,
    get_azure_openai_client,
    get_sync_azure_openai_client,
)
from providers.chat_model import (
    AzureOpenAIGenerator,
    AzureOpenAISummaryGenerator,
    AzureOpenAITitleGenerator,
)
from providers.embeddings import AzureOpenAIEmbeddings
from providers.interfaces import (
    ChatMessage,
    EmbeddingProviderProtocol,
    LLMCompletionResponse,
    LLMProviderProtocol,
)

from providers.mock_ai_generator import (
    MockAIGenerator,
    MockSummaryGenerator,
    MockTitleGenerator,
)

__all__ = [
    "get_azure_openai_client",
    "get_sync_azure_openai_client",
    "close_azure_openai_client",
    "AzureOpenAIGenerator",
    "AzureOpenAITitleGenerator",
    "AzureOpenAISummaryGenerator",
    "MockAIGenerator",
    "MockTitleGenerator",
    "MockSummaryGenerator",
    "AzureOpenAIEmbeddings",
    "ChatMessage",
    "LLMCompletionResponse",
    "LLMProviderProtocol",
    "EmbeddingProviderProtocol",
]
