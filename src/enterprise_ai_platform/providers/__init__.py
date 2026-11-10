"""
External AI model and embedding providers (Azure OpenAI, embeddings).
"""
from enterprise_ai_platform.providers.azure_openai_client import (
    close_azure_openai_client,
    get_azure_openai_client,
    get_sync_azure_openai_client,
)
from enterprise_ai_platform.providers.chat_model import (
    AzureOpenAIGenerator,
    AzureOpenAISummaryGenerator,
    AzureOpenAITitleGenerator,
)
from enterprise_ai_platform.providers.embeddings import AzureOpenAIEmbeddings
from enterprise_ai_platform.providers.interfaces import (
    ChatMessage,
    EmbeddingProviderProtocol,
    LLMCompletionResponse,
    LLMProviderProtocol,
)

__all__ = [
    "get_azure_openai_client",
    "get_sync_azure_openai_client",
    "close_azure_openai_client",
    "AzureOpenAIGenerator",
    "AzureOpenAITitleGenerator",
    "AzureOpenAISummaryGenerator",
    "AzureOpenAIEmbeddings",
    "ChatMessage",
    "LLMCompletionResponse",
    "LLMProviderProtocol",
    "EmbeddingProviderProtocol",
]
