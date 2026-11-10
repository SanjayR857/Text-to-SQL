"""
Unit tests for Azure OpenAI chat models, titling, summarization, and embeddings.
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

from services.conversation.protocols import (
    ContextMessage,
    GenerationContext,
    StreamChunk,
)
from providers.chat_model import (
    AzureOpenAIGenerator,
    AzureOpenAISummaryGenerator,
    AzureOpenAITitleGenerator,
)
from providers.embeddings import AzureOpenAIEmbeddings


@pytest.fixture
def mock_azure_client():
    """Mock AsyncAzureOpenAI client."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.embeddings = MagicMock()
    return client


@pytest.mark.asyncio
async def test_azure_openai_generator_stream(mock_azure_client):
    """Verify AzureOpenAIGenerator streaming with GPT-4o produces StreamChunks."""
    # Setup mock streaming chunks
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock(delta=MagicMock(content="Hello "), finish_reason=None)]
    chunk1.usage = None

    chunk2 = MagicMock()
    chunk2.choices = [MagicMock(delta=MagicMock(content="world!"), finish_reason=None)]
    chunk2.usage = None

    chunk3 = MagicMock()
    chunk3.choices = [MagicMock(delta=MagicMock(content=""), finish_reason="stop")]
    chunk3.usage = MagicMock(prompt_tokens=15, completion_tokens=2)

    async def mock_stream(*args, **kwargs):
        for c in [chunk1, chunk2, chunk3]:
            yield c

    mock_azure_client.chat.completions.create = AsyncMock(side_effect=mock_stream)

    generator = AzureOpenAIGenerator(
        client=mock_azure_client,
        deployment_name="gpt-4o",
    )

    context = GenerationContext(
        conversation_id=uuid4(),
        user_id=uuid4(),
        latest_summary="Existing summary",
        messages=[ContextMessage(role="user", content="Hi", sequence_number=1)],
    )

    chunks: list[StreamChunk] = []
    async for chunk in generator.generate_stream(context, prompt="What is 2+2?"):
        chunks.append(chunk)

    assert len(chunks) == 3
    assert chunks[0].delta == "Hello "
    assert chunks[1].delta == "world!"
    assert chunks[2].is_finish is True
    assert chunks[2].finish_reason == "stop"
    assert chunks[2].model_name == "gpt-4o"
    assert chunks[2].prompt_tokens == 15
    assert chunks[2].completion_tokens == 2


@pytest.mark.asyncio
async def test_azure_openai_title_generator(mock_azure_client):
    """Verify AzureOpenAITitleGenerator uses GPT-4o-mini to generate concise titles."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Financial Report Summary"))
    ]
    mock_azure_client.chat.completions.create = AsyncMock(return_value=mock_response)

    title_gen = AzureOpenAITitleGenerator(
        client=mock_azure_client,
        deployment_name="gpt-4o-mini",
    )

    title = await title_gen.generate_title(
        user_prompt="Can you summarize the Q3 financial report?",
        assistant_response="Here is the summary of Q3 revenue and EBITDA...",
    )

    assert title == "Financial Report Summary"
    mock_azure_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_azure_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_azure_openai_summary_generator(mock_azure_client):
    """Verify AzureOpenAISummaryGenerator rolling summary using GPT-4o-mini."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="User requested Q3 financials. Assistant provided revenue metrics."))
    ]
    mock_azure_client.chat.completions.create = AsyncMock(return_value=mock_response)

    summary_gen = AzureOpenAISummaryGenerator(
        client=mock_azure_client,
        deployment_name="gpt-4o-mini",
    )

    new_messages = [
        ContextMessage(role="user", content="Show Q3 revenue", sequence_number=1),
        ContextMessage(role="assistant", content="Q3 revenue is $5M", sequence_number=2),
    ]

    summary = await summary_gen.generate_summary(
        existing_summary=None,
        new_messages=new_messages,
    )

    assert "User requested Q3 financials" in summary
    call_kwargs = mock_azure_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_azure_openai_embeddings(mock_azure_client):
    """Verify AzureOpenAIEmbeddings batch and single vector generation with text-embedding-3-small."""
    fake_vector = [0.01] * 1536
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=fake_vector), MagicMock(embedding=fake_vector)]
    mock_azure_client.embeddings.create = AsyncMock(return_value=mock_response)

    embeddings_service = AzureOpenAIEmbeddings(
        client=mock_azure_client,
        deployment_name="text-embedding-3-small",
        dimensions=1536,
    )

    # Test single query embedding
    single_vector = await embeddings_service.embed_query("search financial reports")
    assert len(single_vector) == 1536

    # Test batch embedding
    batch_vectors = await embeddings_service.embed_batch(["text 1", "text 2"])
    assert len(batch_vectors) == 2
    assert len(batch_vectors[0]) == 1536

    call_kwargs = mock_azure_client.embeddings.create.call_args[1]
    assert call_kwargs["model"] == "text-embedding-3-small"
