"""
Pure ASGI middleware for HTTP access logging using structlog.

Measures request latency, captures response status codes, correlates authenticated
caller identifiers (user_id), and safely sanitizes sensitive fields (tokens,
credentials, request/response bodies, and query parameters).
"""
import time
from typing import Any

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger(__name__)

# Endpoints excluded from noisy access logging (e.g., automated health probes)
DEFAULT_EXCLUDED_PATHS = (
    "/api/v1/health",
    "/favicon.ico",
)


class RequestLoggingMiddleware:
    """
    Pure ASGI middleware that records structured HTTP access logs and latencies.
    """

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: tuple[str, ...] = DEFAULT_EXCLUDED_PATHS,
    ) -> None:
        """
        Initialize the request logging middleware.

        Args:
            app: Downstream ASGI application.
            excluded_paths: Paths exempt from access logging.
        """
        self.app = app
        self.excluded_paths = excluded_paths

    def _is_excluded(self, path: str) -> bool:
        """Determine if a path is excluded from access logging."""
        return any(path.startswith(prefix) for prefix in self.excluded_paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process the request, time execution, capture status, and emit structured access log.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        method: str = scope.get("method", "")

        # Skip access logging for excluded endpoints (e.g. liveness/readiness probes)
        if self._is_excluded(path):
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        status_code = 500  # Default if downstream crashes before responding

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            state = scope.get("state", {})
            err_kwargs: dict[str, Any] = {
                "method": method,
                "path": path,
                "status_code": 500,
                "duration_ms": duration_ms,
            }
            if "request_id" in state:
                err_kwargs["request_id"] = state["request_id"]
            logger.exception("http_request_failed", **err_kwargs)
            raise
        else:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Extract caller identity populated by downstream authentication middleware
            state = scope.get("state", {})
            user_context = state.get("user_context")
            identity = state.get("identity")

            log_kwargs: dict[str, Any] = {
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }

            if "request_id" in state:
                log_kwargs["request_id"] = state["request_id"]

            # Prefer user_id (UUID) to avoid logging PII where possible; include email if available
            if user_context and hasattr(user_context, "user_id"):
                log_kwargs["user_id"] = str(user_context.user_id)
            elif identity and hasattr(identity, "email"):
                log_kwargs["user_email"] = identity.email

            # Extract client IP if present
            client = scope.get("client")
            if client and len(client) > 0:
                log_kwargs["client_ip"] = client[0]

            logger.info("http_request_finished", **log_kwargs)
