"""
Centralized OpenTelemetry tracing and metrics observability.

Provides:
- Azure Application Insights integration via azure-monitor-opentelemetry
- Generic OTLP exporter support (for Jaeger, Grafana Tempo, Prometheus)
- Automatic FastAPI request/response instrumentation
- Clean helpers: get_tracer(), get_meter(), get_current_trace_id(), get_current_span_id()
- Decorator @trace_span for instrumenting sync and async business operations
"""
from collections.abc import Callable
import functools
import inspect
from typing import Any, ParamSpec, TypeVar

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode
import structlog

from core.config import get_settings

logger = structlog.get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

_is_telemetry_initialized = False


def _build_resource() -> Resource:
    """Build OpenTelemetry resource metadata identifying the service and environment."""
    settings = get_settings()
    return Resource.create(
        {
            "service.name": settings.app_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
        }
    )


def setup_telemetry(app: FastAPI | None = None) -> None:
    """
    Initialize OpenTelemetry tracing, metrics, and exporter backends.

    Priority:
    1. Azure Application Insights (if APPLICATIONINSIGHTS_CONNECTION_STRING is set)
    2. Generic OTLP Collector (if OTEL_EXPORTER_OTLP_ENDPOINT is set)
    3. In-memory TracerProvider (default fallback for local development and testing)

    Args:
        app: Optional FastAPI instance to automatically instrument.
    """
    global _is_telemetry_initialized
    settings = get_settings()

    if not settings.enable_telemetry:
        logger.info("Telemetry is disabled via ENABLE_TELEMETRY=False")
        return

    if _is_telemetry_initialized:
        if app is not None:
            instrument_app(app)
        return

    resource = _build_resource()

    # 1. Azure Application Insights
    if settings.applicationinsights_connection_string:
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor

            conn_str = settings.applicationinsights_connection_string.get_secret_value()
            configure_azure_monitor(
                connection_string=conn_str,
                resource=resource,
                disable_logging=True,  # structlog handles application logging
            )
            logger.info("Azure Application Insights telemetry initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize Azure Application Insights", error=str(exc))
            _setup_fallback_provider(resource)

    # 2. Generic OTLP Collector
    elif settings.otel_exporter_otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            # Tracing
            tracer_provider = TracerProvider(resource=resource)
            span_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
            tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
            trace.set_tracer_provider(tracer_provider)

            # Metrics
            metric_exporter = OTLPMetricExporter(endpoint=settings.otel_exporter_otlp_endpoint)
            metric_reader = PeriodicExportingMetricReader(metric_exporter)
            meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
            metrics.set_meter_provider(meter_provider)

            logger.info(
                "OTLP telemetry initialized successfully",
                endpoint=settings.otel_exporter_otlp_endpoint,
            )
        except Exception as exc:
            logger.error("Failed to initialize OTLP telemetry", error=str(exc))
            _setup_fallback_provider(resource)

    # 3. Local Development / Fallback Provider
    else:
        _setup_fallback_provider(resource)
        logger.info(
            "Local OpenTelemetry provider initialized (tracing enabled without remote export)"
        )

    _is_telemetry_initialized = True

    if app is not None:
        instrument_app(app)


def _setup_fallback_provider(resource: Resource) -> None:
    """Configure default SDK tracer and meter providers for safe local operation."""
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    metrics.set_meter_provider(MeterProvider(resource=resource))


def instrument_app(app: FastAPI) -> None:
    """Instrument a FastAPI application with OpenTelemetry middleware."""
    try:
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="/api/v1/health,/favicon.ico",
        )
        logger.info("FastAPI OpenTelemetry instrumentation attached")
    except Exception as exc:
        logger.warning("Could not instrument FastAPI with OpenTelemetry", error=str(exc))


def get_tracer(name: str = "text_to_sql") -> trace.Tracer:
    """Return an OpenTelemetry Tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str = "text_to_sql") -> metrics.Meter:
    """Return an OpenTelemetry Meter instance."""
    return metrics.get_meter(name)


def get_current_trace_id() -> str | None:
    """
    Return the active OpenTelemetry Trace ID formatted as a 32-character hex string.
    Returns None if no active span context exists.
    """
    span = trace.get_current_span()
    context = span.get_span_context()
    if context and context.is_valid:
        return f"{context.trace_id:032x}"
    return None


def get_current_span_id() -> str | None:
    """
    Return the active OpenTelemetry Span ID formatted as a 16-character hex string.
    Returns None if no active span context exists.
    """
    span = trace.get_current_span()
    context = span.get_span_context()
    if context and context.is_valid:
        return f"{context.span_id:016x}"
    return None


def add_span_attributes(attributes: dict[str, Any]) -> None:
    """Add custom key-value attributes to the active span if recording."""
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, str(value) if not isinstance(value, (bool, int, float, str)) else value)


def trace_span(
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to wrap sync or async functions inside an OpenTelemetry trace span.

    Records uncaught exceptions, marks span status to ERROR, and records span latency.

    Usage:
        @trace_span("execute_sql_query", attributes={"sql.dialect": "postgres"})
        async def execute_query(sql: str) -> list[dict]: ...
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        span_name = name or f"{func.__module__}.{func.__qualname__}"
        tracer = get_tracer(func.__module__)

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                with tracer.start_as_current_span(span_name) as span:
                    if attributes and span.is_recording():
                        add_span_attributes(attributes)
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, str(exc)))
                        raise

            return async_wrapper  # type: ignore[return-value]
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                with tracer.start_as_current_span(span_name) as span:
                    if attributes and span.is_recording():
                        add_span_attributes(attributes)
                    try:
                        return func(*args, **kwargs)
                    except Exception as exc:
                        span.record_exception(exc)
                        span.set_status(Status(StatusCode.ERROR, str(exc)))
                        raise

            return sync_wrapper

    return decorator
