"""
Message Feedback API endpoints.

Exposes REST operations for submitting ratings, commentary, and feedback retrieval.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from enterprise_ai_platform.api.dependencies import (
    get_current_user_id,
    get_feedback_service,
)
from enterprise_ai_platform.api.schemas.feedback import (
    FeedbackResponse,
    FeedbackSubmitRequest,
)
from enterprise_ai_platform.chat.feedback_service import FeedbackService

router = APIRouter(prefix="/conversations/{conversation_id}", tags=["Feedback"])


@router.post(
    "/messages/{message_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit or update message feedback",
)
async def submit_feedback(
    conversation_id: UUID,
    message_id: UUID,
    payload: FeedbackSubmitRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    """
    Submit or update evaluation rating and commentary for an assistant response.
    Enforces conversation ownership and validates that the message is a completed assistant turn.
    """
    feedback = await service.submit_feedback(
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=user_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    return FeedbackResponse.model_validate(feedback)


@router.get(
    "/messages/{message_id}/feedback",
    response_model=FeedbackResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Get message feedback",
)
async def get_feedback(
    conversation_id: UUID,
    message_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse | None:
    """Fetch existing feedback submitted by the user on a specific assistant message."""
    feedback = await service.get_feedback(
        conversation_id=conversation_id,
        message_id=message_id,
        user_id=user_id,
    )
    if feedback is None:
        return None
    return FeedbackResponse.model_validate(feedback)


@router.get(
    "/feedback",
    response_model=list[FeedbackResponse],
    status_code=status.HTTP_200_OK,
    summary="List conversation feedback",
)
async def list_conversation_feedback(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: FeedbackService = Depends(get_feedback_service),
) -> list[FeedbackResponse]:
    """Retrieve all feedback records across messages in a conversation."""
    items = await service.list_feedback(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    return [FeedbackResponse.model_validate(f) for f in items]
