"""
Azure OpenAI chat completion and token streaming implementations.

- AzureOpenAIGenerator: primary generation engine using GPT-4o for complex reasoning & streaming
- AzureOpenAITitleGenerator: fast, cost-efficient titling engine using GPT-4o-mini
- AzureOpenAISummaryGenerator: rolling conversation summarizer using GPT-4o-mini
"""
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncAzureOpenAI
import structlog

from core.config import get_settings
from core.observability import trace_span
from services.conversation.protocols import (
    ContextMessage,
    GenerationContext,
    StreamChunk,
)
from providers.azure_openai_client import get_azure_openai_client

logger = structlog.get_logger(__name__)

_DEFAULT_SYSTEM_PROMPT = (
    "You are an enterprise AI assistant specializing in corporate data, documents, and Text-to-SQL. "
    "Provide clear, accurate, and concise answers based on the retrieved context."
)


class AzureOpenAIGenerator:
    """
    Primary AI generation engine using Azure OpenAI GPT-4o.
    Implements AIGeneratorProtocol with real-time SSE token streaming.
    """

    def __init__(
        self,
        client: AsyncAzureOpenAI | None = None,
        deployment_name: str | None = None,
        temperature: float = 0.2,
        system_prompt: str = _DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.client = client
        self.deployment_name = deployment_name or get_settings().azure_openai_chat_deployment
        self.temperature = temperature
        self.system_prompt = system_prompt

    def _get_client(self) -> AsyncAzureOpenAI:
        return self.client or get_azure_openai_client()

    @trace_span("azure_openai.generate_stream")
    async def generate_stream(
        self,
        context: GenerationContext,
        prompt: str,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream completion tokens from Azure OpenAI GPT-4o.
        Assembles historical context, rolling summaries, and user messages.
        """
        client = self._get_client()

        # Assemble dialogue history
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]

        if context.latest_summary:
            messages.append({
                "role": "system",
                "content": f"Prior conversation summary context:\n{context.latest_summary}",
            })

        for msg in context.messages:
            role = "assistant" if msg.role == "assistant" else "user"
            messages.append({"role": role, "content": msg.content})

        messages.append({"role": "user", "content": prompt})

        logger.info(
            "Initiating Azure OpenAI chat stream",
            deployment=self.deployment_name,
            conversation_id=str(context.conversation_id),
            message_count=len(messages),
        )

        prompt_tokens: int | None = None
        completion_tokens: int = 0
        finish_reason: str | None = None

        try:
            response = await client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,  # type: ignore[arg-type]
                temperature=self.temperature,
                stream=True,
                stream_options={"include_usage": True},
            )

            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta_text = choice.delta.content or ""
                    if delta_text:
                        completion_tokens += 1
                        yield StreamChunk(delta=delta_text)

                    if choice.finish_reason:
                        finish_reason = choice.finish_reason

                if hasattr(chunk, "usage") and chunk.usage:
                    prompt_tokens = chunk.usage.prompt_tokens
                    if chunk.usage.completion_tokens:
                        completion_tokens = chunk.usage.completion_tokens

            # Final termination chunk with usage statistics
            yield StreamChunk(
                delta="",
                is_finish=True,
                finish_reason=finish_reason or "stop",
                model_name=self.deployment_name,
                prompt_tokens=prompt_tokens or (len(prompt.split()) + 20),
                completion_tokens=completion_tokens,
            )

        except Exception as exc:
            logger.error(
                "Azure OpenAI chat streaming error",
                error=str(exc),
                deployment=self.deployment_name,
                conversation_id=str(context.conversation_id),
            )
            raise


class AzureOpenAITitleGenerator:
    """
    Fast conversation title generator using Azure OpenAI GPT-4o-mini.
    Implements TitleGeneratorProtocol.
    """

    def __init__(
        self,
        client: AsyncAzureOpenAI | None = None,
        deployment_name: str | None = None,
    ) -> None:
        self.client = client
        self.deployment_name = deployment_name or get_settings().azure_openai_mini_deployment

    def _get_client(self) -> AsyncAzureOpenAI:
        return self.client or get_azure_openai_client()

    @trace_span("azure_openai.generate_title")
    async def generate_title(
        self,
        user_prompt: str,
        assistant_response: str,
    ) -> str:
        """Generate a concise 3-6 word title using the fast mini model."""
        client = self._get_client()

        messages = [
            {
                "role": "system",
                "content": (
                    "Generate a concise, 3 to 6 word title summarizing the user query and topic. "
                    "Return ONLY the title text with no quotation marks, punctuation, or preamble."
                ),
            },
            {
                "role": "user",
                "content": f"User Prompt: {user_prompt[:500]}\nAssistant snippet: {assistant_response[:300]}",
            },
        ]

        try:
            response = await client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=25,
                temperature=0.3,
            )
            title = response.choices[0].message.content or ""
            clean_title = title.strip().strip('"').strip("'")
            return clean_title if clean_title else "New Conversation"
        except Exception as exc:
            logger.warning("Azure OpenAI titling failed, using fallback", error=str(exc))
            words = user_prompt.strip().split()[:5]
            return " ".join(words).title() if words else "New Conversation"


class AzureOpenAISummaryGenerator:
    """
    Rolling conversation summarizer using Azure OpenAI GPT-4o-mini.
    Implements SummaryGeneratorProtocol.
    """

    def __init__(
        self,
        client: AsyncAzureOpenAI | None = None,
        deployment_name: str | None = None,
    ) -> None:
        self.client = client
        self.deployment_name = deployment_name or get_settings().azure_openai_mini_deployment

    def _get_client(self) -> AsyncAzureOpenAI:
        return self.client or get_azure_openai_client()

    @trace_span("azure_openai.generate_summary")
    async def generate_summary(
        self,
        existing_summary: str | None,
        new_messages: list[ContextMessage],
    ) -> str:
        """Incorporate new messages into a rolling conversational summary using GPT-4o-mini."""
        client = self._get_client()

        formatted_dialogue = "\n".join(
            f"[{msg.role.upper()}]: {msg.content}" for msg in new_messages
        )

        user_content = (
            f"Prior summary:\n{existing_summary or 'None'}\n\n"
            f"New messages to incorporate:\n{formatted_dialogue}"
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a conversation summarizer. Update the rolling summary to capture "
                    "key decisions, entities, user intent, and data queried. Keep it under 200 words."
                ),
            },
            {"role": "user", "content": user_content},
        ]

        try:
            response = await client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=250,
                temperature=0.3,
            )
            summary = response.choices[0].message.content or ""
            return summary.strip()
        except Exception as exc:
            logger.warning("Azure OpenAI summarization failed, preserving existing", error=str(exc))
            return existing_summary or f"Summarized {len(new_messages)} dialogue turns."
