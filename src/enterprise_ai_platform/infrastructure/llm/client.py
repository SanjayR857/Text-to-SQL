"""
Azure OpenAI client factory and connection manager.

Provides singleton AsyncAzureOpenAI and sync AzureOpenAI clients supporting both
API key authentication (for local dev/testing) and Microsoft Entra ID / Azure Managed
Identity (for secure staging/production environments).
"""
import threading
from typing import Any

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI, AzureOpenAI
import structlog

from enterprise_ai_platform.core.config import get_settings

logger = structlog.get_logger(__name__)

_COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"

_async_client: AsyncAzureOpenAI | None = None
_sync_client: AzureOpenAI | None = None
_lock = threading.Lock()


def get_azure_openai_client() -> AsyncAzureOpenAI:
    """
    Return the singleton AsyncAzureOpenAI client.
    Thread-safe lazy initialization.
    """
    global _async_client
    if _async_client is not None:
        return _async_client

    with _lock:
        if _async_client is not None:
            return _async_client

        settings = get_settings()
        endpoint = settings.azure_openai_endpoint.rstrip("/")
        api_key = settings.azure_openai_api_key.get_secret_value() if settings.azure_openai_api_key else None

        client_kwargs: dict[str, Any] = {
            "azure_endpoint": endpoint,
            "api_version": settings.azure_openai_api_version,
            "max_retries": 3,
            "timeout": 60.0,
        }

        if api_key:
            client_kwargs["api_key"] = api_key
            logger.info(
                "Initializing Azure OpenAI client with API Key authentication",
                endpoint=endpoint,
                api_version=settings.azure_openai_api_version,
            )
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                _COGNITIVE_SERVICES_SCOPE,
            )
            client_kwargs["azure_ad_token_provider"] = token_provider
            logger.info(
                "Initializing Azure OpenAI client with Managed Identity authentication",
                endpoint=endpoint,
                api_version=settings.azure_openai_api_version,
            )

        _async_client = AsyncAzureOpenAI(**client_kwargs)
        return _async_client


def get_sync_azure_openai_client() -> AzureOpenAI:
    """
    Return the singleton synchronous AzureOpenAI client.
    Used by synchronous worker jobs or offline document ingestion routines.
    """
    global _sync_client
    if _sync_client is not None:
        return _sync_client

    with _lock:
        if _sync_client is not None:
            return _sync_client

        settings = get_settings()
        endpoint = settings.azure_openai_endpoint.rstrip("/")
        api_key = settings.azure_openai_api_key.get_secret_value() if settings.azure_openai_api_key else None

        client_kwargs: dict[str, Any] = {
            "azure_endpoint": endpoint,
            "api_version": settings.azure_openai_api_version,
            "max_retries": 3,
            "timeout": 60.0,
        }

        if api_key:
            client_kwargs["api_key"] = api_key
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                _COGNITIVE_SERVICES_SCOPE,
            )
            client_kwargs["azure_ad_token_provider"] = token_provider

        _sync_client = AzureOpenAI(**client_kwargs)
        return _sync_client


async def close_azure_openai_client() -> None:
    """Gracefully close the async Azure OpenAI client connections."""
    global _async_client
    with _lock:
        if _async_client is not None:
            await _async_client.close()
            _async_client = None
            logger.info("Closed Azure OpenAI async client")
