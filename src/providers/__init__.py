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
