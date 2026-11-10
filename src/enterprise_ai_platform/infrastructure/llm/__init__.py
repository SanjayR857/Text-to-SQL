"""
Azure OpenAI LLM and embeddings package.

Exports:
- AzureOpenAIGenerator: GPT-4o streaming chat completions
- AzureOpenAITitleGenerator: GPT-4o-mini fast titling
- AzureOpenAISummaryGenerator: GPT-4o-mini rolling conversation summarization
- AzureOpenAIEmbeddings: text-embedding-3-small vector embeddings (1536 dim)
- get_azure_openai_client: singleton AsyncAzureOpenAI client factory
- close_azure_openai_client: client connection disposal
"""
from enterprise_ai_platform.infrastructure.llm.chat_model import (
    AzureOpenAIGenerator,
    AzureOpenAISummaryGenerator,
    AzureOpenAITitleGenerator,
)
from enterprise_ai_platform.infrastructure.llm.client import (
    close_azure_openai_client,
    get_azure_openai_client,
    get_sync_azure_openai_client,
)
from enterprise_ai_platform.infrastructure.llm.embeddings import AzureOpenAIEmbeddings

__all__ = [
    "AzureOpenAIGenerator",
    "AzureOpenAITitleGenerator",
    "AzureOpenAISummaryGenerator",
    "AzureOpenAIEmbeddings",
    "get_azure_openai_client",
    "get_sync_azure_openai_client",
    "close_azure_openai_client",
]
