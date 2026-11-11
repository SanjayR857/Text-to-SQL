"""
Unit tests for core logging configuration and structlog renderers.
"""
import io
import json
import logging

import structlog

from core.observability import setup_logging


def test_setup_logging_json_renderer():
    """Verify that in non-development mode, logs are formatted as valid JSON."""
    setup_logging(log_level="INFO", is_development=False)
    logger = structlog.get_logger("test_json")

    # Capture standard library logging output
    log_output = io.StringIO()
    handler = logging.StreamHandler(log_output)
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ]
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    try:
        logger.info("test_json_event", key1="value1", num=42)
        lines = [line for line in log_output.getvalue().splitlines() if line.strip()]
        assert len(lines) > 0
        parsed = json.loads(lines[-1])
        assert parsed["event"] == "test_json_event"
        assert parsed["key1"] == "value1"
        assert parsed["num"] == 42
    finally:
        logging.getLogger().removeHandler(handler)


def test_censor_sensitive_data():
    """Verify that credentials and sensitive tokens are masked."""
    from core.observability.logging import censor_sensitive_data

    event_dict = {
        "event": "user_auth",
        "username": "alice",
        "password": "super-secret-password",
        "access_token": "jwt.header.payload.signature",
        "api_key": "sk-12345",
        "client_secret": "my-secret",
        "safe_field": "public_data",
    }
    censored = censor_sensitive_data(logging.getLogger(), "info", event_dict)

    assert censored["username"] == "alice"
    assert censored["safe_field"] == "public_data"
    assert censored["password"] == "[REDACTED]"
    assert censored["access_token"] == "[REDACTED]"
    assert censored["api_key"] == "[REDACTED]"
    assert censored["client_secret"] == "[REDACTED]"


def test_inject_open_telemetry_spans():
    """Verify that active OpenTelemetry spans inject trace_id and span_id."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from core.observability.logging import inject_open_telemetry_spans

    provider = TracerProvider()
    tracer = provider.get_tracer("test_tracer")

    with tracer.start_as_current_span("test_span") as span:
        ctx = span.get_span_context()
        event_dict = {"event": "traced_action"}
        result = inject_open_telemetry_spans(logging.getLogger(), "info", event_dict)

        assert "trace_id" in result
        assert "span_id" in result
        assert result["trace_id"] == f"{ctx.trace_id:032x}"
        assert result["span_id"] == f"{ctx.span_id:016x}"



def test_setup_logging_level_filtering():
    """Verify that log messages below the configured level are filtered out."""
    setup_logging(log_level="WARNING", is_development=False)
    logger = structlog.get_logger("test_level")

    log_output = io.StringIO()
    handler = logging.StreamHandler(log_output)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ]
        )
    )
    logging.getLogger().addHandler(handler)

    try:
        logger.info("should_be_filtered_out")
        logger.warning("should_be_logged")
        output = log_output.getvalue()
        assert "should_be_filtered_out" not in output
        assert "should_be_logged" in output
    finally:
        logging.getLogger().removeHandler(handler)

