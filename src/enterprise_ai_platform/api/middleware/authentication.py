"""
Authentication and user-context resolution ASGI middleware.

Intercepts incoming HTTP requests, establishes caller identity via
development headers (or future JWT token validation), resolves the
user context from PostgreSQL, and attaches it to request.state.
"""
from collections.abc import Callable
import re
import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from enterprise_ai_platform.application.authorization.services.user_context_service import (
    UserContextService,
)
from enterprise_ai_platform.core.config import Settings, get_settings
from enterprise_ai_platform.core.exceptions import (
    DatabaseUnavailableError,
    InvalidIdentityError,
    NoActiveAssignmentsError,
    UserNotFoundError,
)
from enterprise_ai_platform.domain.identity.user import RequestIdentity
from enterprise_ai_platform.infrastructure.database.repositories.user_context_repository import (
    UserContextRepository,
)
from enterprise_ai_platform.infrastructure.database.session import get_session_factory

logger = structlog.get_logger(__name__)

# Development identity header name
DEV_USER_EMAIL_HEADER = "x-dev-user-email"

# Public path prefixes exempt from authentication
PUBLIC_PATH_PREFIXES = (
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/favicon.ico",
)

# RFC 5322-compliant basic email syntax validation regex
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware responsible for establishing caller identity and resolving user context.

    Fails closed:
      - 401 Unauthorized if identity header is missing or malformed on protected routes.
      - 403 Forbidden if development authentication is disabled or user has no active roles.
      - 404 Not Found if user email does not exist in the platform users table.
      - 503 Service Unavailable if database is unreachable.

    On successful resolution, attaches:
      - RequestIdentity to request.state.identity
      - UserContext to request.state.user_context
    """

    def __init__(
        self,
        app: ASGIApp,
        settings: Settings | None = None,
        public_prefixes: tuple[str, ...] = PUBLIC_PATH_PREFIXES,
    ) -> None:
        super().__init__(app)
        self._settings = settings or get_settings()
        self._public_prefixes = public_prefixes

    def _is_public_path(self, path: str) -> bool:
        """Check if the requested URL path is exempt from authentication."""
        return any(path.startswith(prefix) for prefix in self._public_prefixes)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """
        Intercept request, resolve caller identity and UserContext, and attach to request.state.
        """
        # 1. Exempt public endpoints
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # 2. Extract development identity header
        raw_email = request.headers.get(DEV_USER_EMAIL_HEADER)

        # 3. Missing identity: fail closed with 401
        if raw_email is None:
            logger.warning(
                "auth_middleware.missing_identity",
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required: missing identity header."},
            )

        # 4. Check if development authentication is permitted
        if not self._settings.allow_dev_auth or self._settings.is_production:
            logger.warning(
                "auth_middleware.dev_auth_disabled",
                path=request.url.path,
                allow_dev_auth=self._settings.allow_dev_auth,
                environment=self._settings.environment,
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Development authentication is disabled."},
            )

        # 5. Validate and normalize email
        clean_email = raw_email.strip().lower()
        if not clean_email or not EMAIL_REGEX.match(clean_email):
            logger.warning(
                "auth_middleware.invalid_email_format",
                path=request.url.path,
                email=clean_email,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid identity email format."},
            )

        # 6. Construct RequestIdentity and attach to request.state
        identity = RequestIdentity(
            email=clean_email,
            auth_method="dev_header",
        )
        request.state.identity = identity
        request.state.user_email = clean_email

        # 7. Resolve UserContext within an isolated, short-lived async database session
        session_factory = get_session_factory()
        try:
            async with session_factory() as session:
                repo = UserContextRepository(session)
                service = UserContextService(repo)
                user_context = await service.resolve_user_context(clean_email)

            # Attach resolved UserContext to request state
            request.state.user_context = user_context

        except UserNotFoundError as exc:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": exc.message},
            )
        except NoActiveAssignmentsError as exc:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": exc.message},
            )
        except InvalidIdentityError as exc:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": exc.message},
            )
        except DatabaseUnavailableError:
            logger.error(
                "auth_middleware.database_unavailable",
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"detail": "Authentication service is currently unavailable. Please try again later."},
            )
        except Exception as exc:
            logger.exception(
                "auth_middleware.unexpected_error",
                path=request.url.path,
                error=str(exc),
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "An unexpected error occurred during authentication processing."},
            )

        return await call_next(request)
