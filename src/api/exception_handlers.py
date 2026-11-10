"""
Global exception handlers for the Chat / Conversation Management Module.

Maps domain exceptions to standard HTTP error responses.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from core.exceptions import (
    ChatDomainException,
    ConversationNotFoundError,
    DuplicateMessageError,
    GenerationConflictError,
    GenerationFencingError,
    InvalidFeedbackError,
    MessageNotFoundError,
    StaleSummaryError,
)


def register(app: FastAPI) -> None:
    """Master exception handler registration."""
    register_chat_exception_handlers(app)


def register_chat_exception_handlers(app: FastAPI) -> None:
    """Register domain exception handlers on the FastAPI application."""

    @app.exception_handler(ConversationNotFoundError)
    async def conversation_not_found_handler(
        request: Request, exc: ConversationNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Conversation not found or access denied."},
        )

    @app.exception_handler(MessageNotFoundError)
    async def message_not_found_handler(
        request: Request, exc: MessageNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Message not found."},
        )

    @app.exception_handler(GenerationConflictError)
    async def generation_conflict_handler(
        request: Request, exc: GenerationConflictError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Generation currently in progress for this conversation."},
        )

    @app.exception_handler(GenerationFencingError)
    async def generation_fencing_handler(
        request: Request, exc: GenerationFencingError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Active generation was cancelled or superseded."},
        )

    @app.exception_handler(DuplicateMessageError)
    async def duplicate_message_handler(
        request: Request, exc: DuplicateMessageError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Duplicate message submission detected.",
                "existing_message_id": str(exc.existing_message_id),
            },
        )

    @app.exception_handler(InvalidFeedbackError)
    async def invalid_feedback_handler(
        request: Request, exc: InvalidFeedbackError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )

    @app.exception_handler(StaleSummaryError)
    async def stale_summary_handler(
        request: Request, exc: StaleSummaryError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.message},
        )

    @app.exception_handler(ChatDomainException)
    async def generic_chat_domain_handler(
        request: Request, exc: ChatDomainException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message},
        )
