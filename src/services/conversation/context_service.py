"""
Context service.

Assembles prior dialogue history and rolling summary into a GenerationContext
for downstream external AI generation engines.
"""
from uuid import UUID

from core.exceptions import ConversationNotFoundError
from services.conversation.protocols import ContextMessage, GenerationContext
from repositories.conversation_repo import (
    ConversationRepository,
)
from repositories.message_repo import (
    MessageRepository,
)
from repositories.summary_repo import (
    SummaryRepository,
)


class ContextService:
    """Service responsible for dialogue context assembly and window formatting."""

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
        summary_repo: SummaryRepository,
    ) -> None:
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.summary_repo = summary_repo

    async def assemble_context(
        self,
        conversation_id: UUID,
        user_id: UUID,
        current_sequence: int,
        max_messages: int = 50,
    ) -> GenerationContext:
        """
        Build GenerationContext from dialogue history prior to the current turn (sequence < current_sequence).
        Includes the latest active summary if available.
        """
        conversation = await self.conversation_repo.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)

        # 1. Fetch latest rolling summary
        latest_summary_entity = await self.summary_repo.get_latest(conversation_id)
        summary_text = latest_summary_entity.summary if latest_summary_entity else None

        # 2. Fetch prior completed messages (strictly before current_sequence)
        prior_messages = await self.message_repo.get_prior_context_messages(
            conversation_id=conversation_id,
            max_sequence=current_sequence - 1,
            limit=max_messages,
        )

        # 3. Transform to neutral domain ContextMessage models
        context_messages = [
            ContextMessage(
                role=msg.role,
                content=msg.content,
                sequence_number=msg.sequence_number,
            )
            for msg in prior_messages
        ]

        return GenerationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            latest_summary=summary_text,
            messages=context_messages,
        )
