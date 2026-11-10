"""
Feedback service.

Coordinates user rating and commentary submission with business validation
and conversation ownership enforcement.
"""
from uuid import UUID

from enterprise_ai_platform.chat.exceptions import (
    ConversationNotFoundError,
    InvalidFeedbackError,
    MessageNotFoundError,
)
from enterprise_ai_platform.chat.models import MessageFeedback
from enterprise_ai_platform.chat.repositories.conversation_repo import (
    ConversationRepository,
)
from enterprise_ai_platform.chat.repositories.feedback_repo import (
    FeedbackRepository,
)
from enterprise_ai_platform.chat.repositories.message_repo import (
    MessageRepository,
)


class FeedbackService:
    """Service governing message evaluation and feedback submission."""

    def __init__(
        self,
        feedback_repo: FeedbackRepository,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
    ) -> None:
        self.feedback_repo = feedback_repo
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo

    async def submit_feedback(
        self,
        conversation_id: UUID,
        message_id: UUID,
        user_id: UUID,
        rating: int,
        comment: str | None = None,
    ) -> MessageFeedback:
        """
        Submit rating and commentary for an assistant response.

        Validation rules:
        1. Rating must be an integer between 1 and 5.
        2. Conversation must exist and be owned by the requesting user.
        3. Message must belong to the conversation.
        4. Message role must be 'assistant' and status must be 'completed'.
        """
        # Rule 1: Rating range
        if not (1 <= rating <= 5):
            raise InvalidFeedbackError(f"Rating must be between 1 and 5; received {rating}.")

        # Rule 2: Conversation ownership
        conversation = await self.conversation_repo.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)

        # Rule 3: Message existence in conversation
        message = await self.message_repo.get_by_id(message_id, conversation_id)
        if message is None:
            raise MessageNotFoundError(message_id)

        # Rule 4: Must evaluate completed assistant message
        if message.role != "assistant":
            raise InvalidFeedbackError("Feedback can only be submitted on assistant responses.")
        if message.status != "completed":
            raise InvalidFeedbackError(
                f"Cannot submit feedback on message in '{message.status}' status. Only 'completed' messages can be rated."
            )

        # Persist feedback via composite upsert
        return await self.feedback_repo.upsert(
            message_id=message_id,
            conversation_id=conversation_id,
            user_id=user_id,
            rating=rating,
            comment=comment.strip() if comment else None,
        )

    async def get_feedback(
        self,
        conversation_id: UUID,
        message_id: UUID,
        user_id: UUID,
    ) -> MessageFeedback | None:
        """Fetch user feedback on a message, verifying conversation ownership."""
        conversation = await self.conversation_repo.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)

        return await self.feedback_repo.get_by_message_and_user(message_id, user_id)

    async def list_feedback(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> list[MessageFeedback]:
        """List all feedback records in a conversation owned by the requesting user."""
        conversation = await self.conversation_repo.get_by_id(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)

        return await self.feedback_repo.get_by_conversation(conversation_id)
