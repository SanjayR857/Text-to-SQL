"""
Default / mock AI generator implementations for testing and development.
"""
import asyncio
from collections.abc import AsyncIterator

from enterprise_ai_platform.domain.chat.protocols import (
    ContextMessage,
    GenerationContext,
    StreamChunk,
)


class MockAIGenerator:
    """Simulated AI generator that streams canned token responses."""

    def __init__(self, delay_per_chunk: float = 0.01) -> None:
        self.delay_per_chunk = delay_per_chunk

    async def generate_stream(
        self,
        context: GenerationContext,
        prompt: str,
    ) -> AsyncIterator[StreamChunk]:
        """Stream simulated tokens."""
        tokens = ["This ", "is ", "a ", "simulated ", "AI ", "response ", "to: ", f"'{prompt}'."]
        for token in tokens:
            if self.delay_per_chunk > 0:
                await asyncio.sleep(self.delay_per_chunk)
            yield StreamChunk(delta=token)

        yield StreamChunk(
            delta="",
            is_finish=True,
            finish_reason="stop",
            prompt_tokens=10,
            completion_tokens=len(tokens),
        )


class MockTitleGenerator:
    """Simulated title generator producing a concise conversation title."""

    async def generate_title(
        self,
        user_prompt: str,
        assistant_response: str,
    ) -> str:
        """Generate a concise title based on first user prompt."""
        clean_prompt = user_prompt.strip()
        words = clean_prompt.split()[:5]
        return " ".join(words).title() if words else "Conversation Turn"


class MockSummaryGenerator:
    """Simulated summary generator producing a rolling context summary."""

    async def generate_summary(
        self,
        existing_summary: str | None,
        new_messages: list[ContextMessage],
    ) -> str:
        """Combine prior summary with count of newly summarized messages."""
        msg_count = len(new_messages)
        if existing_summary:
            return f"{existing_summary} [Followed by {msg_count} additional messages]."
        return f"Summary of the first {msg_count} dialogue messages."
