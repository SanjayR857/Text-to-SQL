"""
FastAPI dependency injection providers.
"""
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from enterprise_ai_platform.application.chat.context_service import ContextService
from enterprise_ai_platform.application.chat.conversation_service import (
    ConversationService,
)
from enterprise_ai_platform.application.chat.feedback_service import FeedbackService
from enterprise_ai_platform.application.chat.message_service import MessageService
from enterprise_ai_platform.application.chat.streaming_orchestrator import (
    StreamingOrchestrator,
)
from enterprise_ai_platform.core.config import get_settings
from enterprise_ai_platform.domain.chat.protocols import (
    AIGeneratorProtocol,
    SummaryGeneratorProtocol,
    TitleGeneratorProtocol,
)
from enterprise_ai_platform.infrastructure.database.repositories.conversation_repo import (
    ConversationRepository,
)
from enterprise_ai_platform.infrastructure.database.repositories.feedback_repo import (
    FeedbackRepository,
)
from enterprise_ai_platform.infrastructure.database.repositories.message_repo import (
    MessageRepository,
)
from enterprise_ai_platform.infrastructure.database.repositories.summary_repo import (
    SummaryRepository,
)
from enterprise_ai_platform.infrastructure.database.session import (
    get_db_session,
    get_session_factory,
)
from enterprise_ai_platform.infrastructure.streaming.mock_ai_generator import (
    MockAIGenerator,
    MockSummaryGenerator,
    MockTitleGenerator,
)

# Fallback development user UUID
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> UUID:
    """
    Extract authenticated user UUID from request context.

    In production/staging: Must receive an authenticated principal identity.
    In development mode: Falls back to DEV_USER_ID if X-User-ID is omitted.
    """
    if x_user_id is not None:
        try:
            return UUID(x_user_id)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-User-ID format; must be a valid UUID.",
            ) from err

    settings = get_settings()
    if settings.is_development:
        return DEV_USER_ID

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required: X-User-ID header missing.",
    )


def get_conversation_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ConversationRepository:
    """Dependency provider for ConversationRepository."""
    return ConversationRepository(session)


def get_message_repo(
    session: AsyncSession = Depends(get_db_session),
) -> MessageRepository:
    """Dependency provider for MessageRepository."""
    return MessageRepository(session)


def get_summary_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SummaryRepository:
    """Dependency provider for SummaryRepository."""
    return SummaryRepository(session)


def get_feedback_repo(
    session: AsyncSession = Depends(get_db_session),
) -> FeedbackRepository:
    """Dependency provider for FeedbackRepository."""
    return FeedbackRepository(session)


def get_conversation_service(
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
) -> ConversationService:
    """Dependency provider for ConversationService."""
    return ConversationService(conv_repo)


def get_message_service(
    msg_repo: MessageRepository = Depends(get_message_repo),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
) -> MessageService:
    """Dependency provider for MessageService."""
    return MessageService(msg_repo, conv_repo)


def get_context_service(
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
    msg_repo: MessageRepository = Depends(get_message_repo),
    summary_repo: SummaryRepository = Depends(get_summary_repo),
) -> ContextService:
    """Dependency provider for ContextService."""
    return ContextService(conv_repo, msg_repo, summary_repo)


def get_feedback_service(
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
    conv_repo: ConversationRepository = Depends(get_conversation_repo),
    msg_repo: MessageRepository = Depends(get_message_repo),
) -> FeedbackService:
    """Dependency provider for FeedbackService."""
    return FeedbackService(feedback_repo, conv_repo, msg_repo)


def get_session_factory_provider() -> async_sessionmaker[AsyncSession]:
    """Dependency provider returning the singleton async sessionmaker."""
    return get_session_factory()


def get_ai_generator() -> AIGeneratorProtocol:
    """
    Dependency provider for external AI generation engine.
    Returns MockAIGenerator by default; overridden in staging/production with real AI engine.
    """
    return MockAIGenerator()


def get_title_generator() -> TitleGeneratorProtocol | None:
    """Dependency provider for conversation title generator."""
    return MockTitleGenerator()


def get_summary_generator() -> SummaryGeneratorProtocol | None:
    """Dependency provider for rolling conversation summary generator."""
    return MockSummaryGenerator()


def get_streaming_orchestrator(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory_provider),
    ai_generator: AIGeneratorProtocol = Depends(get_ai_generator),
    title_generator: TitleGeneratorProtocol | None = Depends(get_title_generator),
    summary_generator: SummaryGeneratorProtocol | None = Depends(get_summary_generator),
) -> StreamingOrchestrator:
    """Dependency provider for StreamingOrchestrator."""
    return StreamingOrchestrator(
        session_factory=session_factory,
        ai_generator=ai_generator,
        title_generator=title_generator,
        summary_generator=summary_generator,
    )
