"""
Centralized structured logging configuration using structlog.

Provides structured JSON logging in staging/production environments and
human-readable, colorized console logging in local development. Integrates with
Python's standard library logging and supports contextvars propagation.
"""
import logging
import sys

import structlog

from enterprise_ai_platform.core.config import get_settings


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
