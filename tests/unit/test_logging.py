"""
Unit tests for core logging configuration and structlog renderers.
"""
import io
import json
import logging

import structlog

from core.logging import setup_logging


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
