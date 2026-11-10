"""
Shared cross-cutting concerns: configuration, logging, exceptions, and telemetry.
"""
from enterprise_ai_platform.core.config import Settings, get_settings
from enterprise_ai_platform.core.logging import setup_logging
from enterprise_ai_platform.core.telemetry import (
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
    "setup_logging",
    "setup_telemetry",
    "get_tracer",
    "get_meter",
    "get_current_trace_id",
    "get_current_span_id",
    "add_span_attributes",
    "trace_span",
]

