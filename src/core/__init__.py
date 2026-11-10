"""
Shared cross-cutting concerns: configuration, logging, exceptions, telemetry, database, and events.
"""
from core.config import Settings, get_settings
from core.database import (
    Base,
    async_db_session,
    check_connection,
    close_engine,
    get_async_engine,
    get_db_session,
    get_session_factory,
    reset_session_factory,
)
from core.events import InMemoryEventBus
from core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ColumnAccessDeniedError,
    DatabaseUnavailableError,
    DevAuthDisabledError,
    InvalidIdentityError,
    JoinAccessDeniedError,
    MissingIdentityError,
    NoActiveAssignmentsError,
    PlatformException,
    SqlSecurityError,
    TableAccessDeniedError,
    UserNotFoundError,
)
from core.logging import setup_logging
from core.telemetry import (
    add_span_attributes,
    get_current_span_id,
    get_current_trace_id,
    get_meter,
    get_tracer,
    setup_telemetry,
    trace_span,
)

__all__ = [
    "Settings",
    "get_settings",
    "Base",
    "get_async_engine",
    "close_engine",
    "check_connection",
    "get_session_factory",
    "reset_session_factory",
    "get_db_session",
    "async_db_session",
    "InMemoryEventBus",
    "PlatformException",
    "AuthenticationError",
    "MissingIdentityError",
    "InvalidIdentityError",
    "DevAuthDisabledError",
    "UserNotFoundError",
    "NoActiveAssignmentsError",
    "DatabaseUnavailableError",
    "AuthorizationError",
    "TableAccessDeniedError",
    "ColumnAccessDeniedError",
    "JoinAccessDeniedError",
    "SqlSecurityError",
    "setup_logging",
    "setup_telemetry",
    "get_tracer",
    "get_meter",
    "get_current_trace_id",
    "get_current_span_id",
    "add_span_attributes",
    "trace_span",
]
