"""
Centralized structured logging configuration using structlog.

Provides structured JSON logging in staging/production environments and
human-readable, colorized console logging in local development. Integrates with
Python's standard library logging, supports contextvars propagation, automatic
OpenTelemetry trace correlation, and PII/secret scrubbing.
"""
import logging
import sys
from typing import Any

from opentelemetry import trace
import structlog

from core.config import get_settings

DEFAULT_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "api_key",
        "apikey",
        "client_secret",
        "private_key",
    }
)


def inject_open_telemetry_spans(
    logger: logging.Logger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """
    Inject active OpenTelemetry trace_id and span_id into the log record.

    Enables distributed tracing correlation across observability platforms
    (e.g., Azure Application Insights, Datadog, Grafana Tempo/Loki).
    """
    try:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = f"{ctx.trace_id:032x}"
            event_dict["span_id"] = f"{ctx.span_id:016x}"
    except Exception:
        pass
    return event_dict


def censor_sensitive_data(
    logger: logging.Logger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """
    Scrub sensitive keys and credential tokens from the structured log payload.

    Replaces matching sensitive values with '[REDACTED]'.
    """
    for key in list(event_dict.keys()):
        if isinstance(key, str) and any(s in key.lower() for s in DEFAULT_SENSITIVE_KEYS):
            event_dict[key] = "[REDACTED]"
    return event_dict


def setup_logging(
    log_level: str | None = None,
    is_development: bool | None = None,
) -> None:
    """
    Configure standard logging and structlog for the application.

    Args:
        log_level: Optional log level string (DEBUG, INFO, WARNING, ERROR).
            Defaults to settings.log_level.
        is_development: Flag indicating whether development formatting should be used.
            Defaults to settings.is_development.
    """
    settings = get_settings()
    level_str = (log_level or settings.log_level).upper()
    level = getattr(logging, level_str, logging.INFO)
    dev_mode = settings.is_development if is_development is None else is_development

    # Shared processors executed for all log records
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        inject_open_telemetry_spans,
        censor_sensitive_data,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if dev_mode:
        # Development: pretty-printed, colorized console formatting
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Staging & Production: structured JSON formatting
        renderer = structlog.processors.JSONRenderer()

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure Python's standard library logging handler
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Silence overly verbose third-party loggers
    for noisy_logger in ("uvicorn.access", "asyncio", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

