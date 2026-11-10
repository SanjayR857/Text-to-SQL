"""
Live integration tests for Azure OpenAI Chat and Embeddings services.

Validates that the live Azure OpenAI / AI Foundry deployment correctly
handles streaming generation and vector embeddings using credentials in .env.
"""
from uuid import uuid4
import pytest

from core.config import get_settings
from services.conversation.protocols import GenerationContext
from providers.chat_model import AzureOpenAIGenerator
from providers.embeddings import AzureOpenAIEmbeddings


def _skip_if_mock_or_missing_creds() -> None:
    settings = get_settings()
    if not settings.azure_openai_api_key or "mock" in settings.azure_openai_endpoint:
        pytest.skip("Live Azure OpenAI credentials not configured.")


@pytest.mark.asyncio
async def test_live_azure_openai_streaming() -> None:
    """Verify live streaming response from the configured Azure OpenAI chat deployment."""
    _skip_if_mock_or_missing_creds()

    generator = AzureOpenAIGenerator()
    context = GenerationContext(
        conversation_id=uuid4(),
        user_id=uuid4(),
        latest_summary=None,
        messages=[],
    )

    chunks = []
    async for chunk in generator.generate_stream(context, prompt="Respond with exactly: OK"):
        chunks.append(chunk)

    assert len(chunks) > 0
    full_response = "".join(chunk.delta for chunk in chunks)
    assert "OK" in full_response
    assert any(chunk.is_finish for chunk in chunks)


@pytest.mark.asyncio
async def test_live_azure_openai_embeddings() -> None:
    """Verify vector generation from the configured Azure OpenAI embeddings deployment."""
    _skip_if_mock_or_missing_creds()

    settings = get_settings()
    embeddings = AzureOpenAIEmbeddings()

    vector = await embeddings.embed_query("Enterprise AI integration test")

    assert len(vector) == settings.embedding_dimensions
    assert all(isinstance(val, float) for val in vector)
