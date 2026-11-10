"""
Enterprise AI Platform – FastAPI application entry point.

Initialises the FastAPI app, registers middleware, routers, and exception handlers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lifespan import lifespan
from api import exception_handlers
from api.middleware import request_id, logging as log_middleware, security_headers
from api.routes import health, auth, conversations, feedback
from core.config import get_settings, settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# Must be added before custom middleware so pre-flight OPTIONS requests are
# handled correctly.  Origins are driven by the CORS_ORIGINS env variable.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Custom middleware (order matters – outermost wrapper is applied first)
# ---------------------------------------------------------------------------
app.add_middleware(security_headers.SecurityHeadersMiddleware)
app.add_middleware(log_middleware.RequestLoggingMiddleware)
app.add_middleware(request_id.RequestIdMiddleware)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
exception_handlers.register(app)
