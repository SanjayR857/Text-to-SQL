"""
Authentication middleware for request identity establishment.

Extracts and validates identity from the development identity header (x-dev-user-email)
when ALLOW_DEV_AUTH is enabled, and attaches a typed RequestIdentity object to request.state.
Designed to be replaced or extended by Azure Entra ID JWT validation in future phases.
"""
from collections.abc import Callable
import re
import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from enterprise_ai_platform.core.config import Settings, get_settings
from enterprise_ai_platform.domain.identity.user import RequestIdentity

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
    ASGI middleware responsible for establishing caller identity.

    Fails closed:
      - 401 Unauthorized if identity header is missing on protected routes.
      - 403 Forbidden if development authentication is disabled or in production.
      - 401 Unauthorized if the provided email format is invalid.

    On successful validation, attaches a RequestIdentity instance to request.state.identity.
    """

    def __init__(
        self,
        app: ASGIApp,
        settings: Settings | None = None,
        public_prefixes: tuple[str, ...] = PUBLIC_PATH_PREFIXES,
    ) -> None:
        """
        Initialize the authentication middleware.

        Args:
            app: ASGI application instance.
            settings: Application settings singleton.
            public_prefixes: Tuple of path prefixes exempt from authentication.
        """
        super().__init__(app)
        self._settings = settings or get_settings()
        self._public_prefixes = public_prefixes

    def _is_public_path(self, path: str) -> bool:
        """Check if the requested URL path is exempt from authentication."""
        return any(path.startswith(prefix) for prefix in self._public_prefixes)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """
        Intercept request, resolve caller identity, and attach to request.state.
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

        logger.debug(
            "auth_middleware.identity_established",
            email=clean_email,
            path=request.url.path,
        )

        return await call_next(request)
