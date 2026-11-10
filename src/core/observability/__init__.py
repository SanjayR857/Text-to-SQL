"""
Observability package unifying structured logging and OpenTelemetry tracing/metrics.
"""
from core.observability.logging import setup_logging
from core.observability.telemetry import (
    add_span_attributes,
    get_current_span_id,
    get_current_trace_id,
    get_meter,
    get_tracer,
    instrument_app,
    setup_telemetry,
    trace_span,
)

__all__ = [
    "setup_logging",
    "setup_telemetry",
    "instrument_app",
    "get_tracer",
    "get_meter",
    "get_current_trace_id",
    "get_current_span_id",
    "add_span_attributes",
    "trace_span",
]
