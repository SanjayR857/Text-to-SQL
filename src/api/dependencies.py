"""
FastAPI dependency injection providers.
"""
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from rbac.role import Role
from rbac.user import RequestIdentity, UserContext

from services.conversation import (
    ContextService,
    ConversationService,
    FeedbackService,
    MessageService,
    StreamingOrchestrator,
)
from core.config import get_settings
from services.conversation.protocols import (
    AIGeneratorProtocol,
    SummaryGeneratorProtocol,
    TitleGeneratorProtocol,
)
from repositories.conversation_repo import (
    ConversationRepository,
)
from repositories.feedback_repo import (
    FeedbackRepository,
)
from repositories.message_repo import (
    MessageRepository,
)
from repositories.summary_repo import (
    SummaryRepository,
)
from core.database import (
    get_db_session,
    get_session_factory,
)
from providers import (
    AzureOpenAIEmbeddings,
    AzureOpenAIGenerator,
    AzureOpenAISummaryGenerator,
    AzureOpenAITitleGenerator,
    MockAIGenerator,
    MockSummaryGenerator,
    MockTitleGenerator,
)

# Fallback development user UUID
DEV_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def get_current_identity(request: Request) -> RequestIdentity:
    """
    Extract authenticated RequestIdentity from request.state.

    Populated upstream by AuthenticationMiddleware.

    Raises:
        HTTPException: 401 if request identity has not been resolved.
    """
    identity: RequestIdentity | None = getattr(request.state, "identity", None)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: request identity not established.",
        )
    return identity


def get_current_user_context(request: Request) -> UserContext:
    """
    Extract resolved UserContext from request.state.

    Populated upstream by AuthenticationMiddleware.

    Raises:
        HTTPException: 401 if user context has not been established.
    """
    context: UserContext | None = getattr(request.state, "user_context", None)
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: user context not established.",
        )
    return context


async def get_current_user_id(
    request: Request,
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> UUID:
    """
    Extract authenticated user UUID from request context.

    Prioritizes the authenticated user_id set by AuthenticationMiddleware.
    Falls back to X-User-ID or DEV_USER_ID for test suites bypassing middleware.
    """
    # 1. Prefer authenticated principal verified by AuthenticationMiddleware
    user_id: UUID | None = getattr(request.state, "user_id", None)
    if user_id is not None:
        return user_id

    context: UserContext | None = getattr(request.state, "user_context", None)
    if context is not None:
        return context.user_id

    # 2. Test harness fallback: explicit header
    if x_user_id is not None:
        try:
            return UUID(x_user_id)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-User-ID format; must be a valid UUID.",
            ) from err

    # 3. Development environment fallback
    settings = get_settings()
    if settings.is_development:
        return DEV_USER_ID

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required: user identity not established.",
    )


def require_ca_admin(
    context: UserContext = Depends(get_current_user_context),
) -> UserContext:
    """
    Enforce Central Application Administrator access.

    Raises:
        HTTPException: 403 Forbidden if user is not a CA Admin.
    """
    if not context.is_ca_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Central Application Administrator access required.",
        )
    return context


def require_vertical_access(
    required_role: Role | None = None,
):
    """
    Dependency factory to enforce vertical-scoped access.

    Args:
        required_role: Specific role required within the vertical (e.g., Role.CHIEF).
                       If None, any active assignment in the vertical is accepted.

    Returns:
        FastAPI dependency callable that checks access against path param `vertical_code`.
    """
    def dependency(
        vertical_code: str,
        context: UserContext = Depends(get_current_user_context),
    ) -> UserContext:
        # Central Application Admins have global access
        if context.is_ca_admin:
            return context

        if required_role is not None:
            if not context.has_role_in_vertical(required_role, vertical_code):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role.value}' required in vertical '{vertical_code.upper()}'.",
                )
        else:
            if not context.has_vertical(vertical_code):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied for vertical '{vertical_code.upper()}'.",
                )
        return context

    return dependency


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
    Returns AzureOpenAIGenerator (GPT-4o) when real endpoint is configured, otherwise MockAIGenerator.
    """
    settings = get_settings()
    if settings.azure_openai_endpoint and "mock" not in settings.azure_openai_endpoint:
        return AzureOpenAIGenerator()
    return MockAIGenerator()


def get_title_generator() -> TitleGeneratorProtocol | None:
    """
    Dependency provider for conversation title generator.
    Returns AzureOpenAITitleGenerator (GPT-4o-mini) when real endpoint is configured.
    """
    settings = get_settings()
    if settings.azure_openai_endpoint and "mock" not in settings.azure_openai_endpoint:
        return AzureOpenAITitleGenerator()
    return MockTitleGenerator()


def get_summary_generator() -> SummaryGeneratorProtocol | None:
    """
    Dependency provider for rolling conversation summary generator.
    Returns AzureOpenAISummaryGenerator (GPT-4o-mini) when real endpoint is configured.
    """
    settings = get_settings()
    if settings.azure_openai_endpoint and "mock" not in settings.azure_openai_endpoint:
        return AzureOpenAISummaryGenerator()
    return MockSummaryGenerator()


def get_embeddings_service() -> AzureOpenAIEmbeddings:
    """Dependency provider for Azure OpenAI vector embeddings service (text-embedding-3-small)."""
    return AzureOpenAIEmbeddings()


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
