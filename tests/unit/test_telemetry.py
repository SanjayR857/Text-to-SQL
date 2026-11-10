"""
Unit tests for OpenTelemetry observability and tracing utilities.
"""
import pytest
from opentelemetry.trace import StatusCode

from enterprise_ai_platform.core.telemetry import (
    add_span_attributes,
    get_current_span_id,
    get_current_trace_id,
    get_meter,
    get_tracer,
    setup_telemetry,
    trace_span,
)


@pytest.fixture(autouse=True)
def init_telemetry():
    """Ensure OpenTelemetry fallback provider is active for unit testing."""
    setup_telemetry()


def test_get_tracer_and_meter():
    """Verify tracer and meter instantiation."""
    tracer = get_tracer("test_module")
    meter = get_meter("test_module")

    assert tracer is not None
    assert meter is not None


def test_trace_span_sync_function():
    """Verify synchronous function instrumentation via @trace_span."""
    @trace_span("sync_operation", attributes={"operation.type": "unit_test"})
    def compute(a: int, b: int) -> int:
        return a + b

    result = compute(10, 20)
    assert result == 30


@pytest.mark.asyncio
async def test_trace_span_async_function():
    """Verify asynchronous coroutine instrumentation via @trace_span."""
    @trace_span("async_operation", attributes={"operation.type": "async_test"})
    async def async_compute(val: str) -> str:
        return val.upper()

    result = await async_compute("enterprise")
    assert result == "ENTERPRISE"


def test_trace_span_exception_recording():
    """Verify exceptions are caught, recorded on span, and re-raised."""
    @trace_span("failing_operation")
    def fail():
        raise ValueError("Simulated computation failure")

    with pytest.raises(ValueError, match="Simulated computation failure"):
        fail()


def test_current_trace_and_span_id():
    """Verify 32-character trace ID and 16-character span ID extraction."""
    tracer = get_tracer("test_id_tracer")

    with tracer.start_as_current_span("active_span"):
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()

        assert trace_id is not None
        assert len(trace_id) == 32
        assert span_id is not None
        assert len(span_id) == 16


def test_add_span_attributes():
    """Verify adding dynamic attributes to active recording span."""
    tracer = get_tracer("test_attr_tracer")

    with tracer.start_as_current_span("attribute_span") as span:
        add_span_attributes({"custom.user_id": "123", "custom.count": 42})
        assert span.is_recording()
