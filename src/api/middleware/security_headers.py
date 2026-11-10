"""
Pure ASGI middleware that injects security-related HTTP response headers.

Applies enterprise security headers following OWASP recommendations:
  - X-Content-Type-Options
  - X-Frame-Options
  - Referrer-Policy
  - Content-Security-Policy
  - Permissions-Policy
  - Strict-Transport-Security (HTTPS / Production only)
"""
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.config import get_settings


class SecurityHeadersMiddleware:
    """
    Pure ASGI middleware that injects hardened security headers into outgoing HTTP responses.
    """

    def __init__(
        self,
        app: ASGIApp,
        is_production: bool | None = None,
        csp_policy: str = "default-src 'self'",
        permissions_policy: str = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
    ) -> None:
        """
        Initialize the security headers middleware.

        Args:
            app: Downstream ASGI application.
            is_production: Whether the application is running in production (controls HSTS).
            csp_policy: Content-Security-Policy string.
            permissions_policy: Permissions-Policy string.
        """
        self.app = app
        settings = get_settings()
        self.is_production = settings.is_production if is_production is None else is_production

        # Pre-compile headers as raw byte tuples for optimal ASGI performance
        self.headers_to_add: list[tuple[bytes, bytes]] = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"strict-origin-when-cross-origin"),
            (b"content-security-policy", csp_policy.encode("latin-1")),
            (b"permissions-policy", permissions_policy.encode("latin-1")),
        ]

        # Only apply HSTS in production to prevent locking out local HTTP development
        if self.is_production:
            self.headers_to_add.append(
                (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Intercept the response and append configured security headers.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing_headers: list[tuple[bytes, bytes]] = list(message.get("headers", []))
                existing_keys = {k.lower() for k, _ in existing_headers}

                for k, v in self.headers_to_add:
                    if k not in existing_keys:
                        existing_headers.append((k, v))

                message["headers"] = existing_headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
