"""
Pure ASGI middleware for Request ID correlation and propagation.

Extracts, validates, or generates a UUID for X-Request-ID, binds it to the
structlog contextvars for distributed tracing, sets it on the request state,
and attaches X-Request-ID to the outgoing HTTP response headers.
"""
from typing import Any
import uuid

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "x-request-id"
REQUEST_ID_HEADER_BYTES = b"x-request-id"


def validate_or_generate_request_id(incoming: str | None) -> str:
    """
    Validate incoming request ID format or generate a fresh UUID.

    Ensures that incoming request IDs conform to valid UUID representation.
    Malformed or excessively long values are rejected and replaced.

    Args:
        incoming: Optional raw header string.

    Returns:
        Validated UUID string.
    """
    if incoming:
        clean = incoming.strip()
        try:
            return str(uuid.UUID(clean))
        except (ValueError, AttributeError):
            pass
    return str(uuid.uuid4())


class RequestIdMiddleware:
    """
    Pure ASGI middleware that enforces request ID correlation across all HTTP requests.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize middleware.

        Args:
            app: Downstream ASGI application.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Process the ASGI request lifecycle.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 1. Extract X-Request-ID from ASGI scope headers
        incoming_id: str | None = None
        for key, value in scope.get("headers", []):
            if key.lower() == REQUEST_ID_HEADER_BYTES:
                incoming_id = value.decode("latin-1")
                break

        # 2. Validate format or generate new UUID
        request_id = validate_or_generate_request_id(incoming_id)

        # 3. Bind to structlog contextvars for logging correlation
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # 4. Attach to request state
        state = scope.setdefault("state", {})
        state["request_id"] = request_id

        # 5. Intercept outgoing response headers to inject X-Request-ID
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers: list[tuple[bytes, bytes]] = list(message.get("headers", []))
                # Add or update X-Request-ID
                headers.append((REQUEST_ID_HEADER_BYTES, request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # 6. Clean up structlog contextvars to prevent leakage between requests
            structlog.contextvars.clear_contextvars()
