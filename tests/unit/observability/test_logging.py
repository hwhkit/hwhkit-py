"""Tests for hwhkit.observability.logging."""

from __future__ import annotations

import io
import json
import logging
from contextlib import redirect_stdout
from typing import Any

import pytest
import structlog
from hwhkit.observability.logging import configure_logging, get_logger


@pytest.fixture(autouse=True)
def _reset_structlog() -> Any:
    """Reset structlog state between tests so configure_logging is reproducible."""
    yield
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()


def _capture(callable_: Any) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        callable_()
    return buf.getvalue()


def test_json_mode_outputs_json() -> None:
    configure_logging(level="INFO", json_mode=True)
    log = get_logger("test")

    out = _capture(lambda: log.info("hello", k="v"))
    line = next(line for line in out.splitlines() if line.strip())
    parsed = json.loads(line)
    assert parsed["event"] == "hello"
    assert parsed["k"] == "v"
    assert parsed["level"] == "info"
    assert "timestamp" in parsed


def test_level_filters_lower_messages() -> None:
    configure_logging(level="WARNING", json_mode=True)
    log = get_logger("test")
    out = _capture(lambda: (log.info("low"), log.warning("high")))
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "high"


def test_service_name_injected() -> None:
    configure_logging(level="INFO", json_mode=True, service_name="trading")
    log = get_logger("test")
    out = _capture(lambda: log.info("evt"))
    parsed = json.loads(next(line for line in out.splitlines() if line.strip()))
    assert parsed["service"] == "trading"


def test_trace_context_injected_when_otel_span_active() -> None:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider

    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer("test")

    configure_logging(level="INFO", json_mode=True)
    log = get_logger("test")

    with tracer.start_as_current_span("op"):
        out = _capture(lambda: log.info("evt"))
    parsed = json.loads(next(line for line in out.splitlines() if line.strip()))
    assert "trace_id" in parsed
    assert "span_id" in parsed
    assert len(parsed["trace_id"]) == 32
    assert len(parsed["span_id"]) == 16


def test_no_trace_context_outside_span() -> None:
    configure_logging(level="INFO", json_mode=True)
    log = get_logger("test")
    out = _capture(lambda: log.info("evt"))
    parsed = json.loads(next(line for line in out.splitlines() if line.strip()))
    assert "trace_id" not in parsed


def test_idempotent_reconfigure() -> None:
    configure_logging(level="INFO", json_mode=True)
    configure_logging(level="DEBUG", json_mode=True)
    log = get_logger("test")
    out = _capture(lambda: log.debug("debug-line"))
    assert any(
        line.strip() and json.loads(line)["event"] == "debug-line" for line in out.splitlines()
    )


def test_get_logger_returns_bound_logger() -> None:
    configure_logging(level="INFO", json_mode=True)
    log = get_logger("trading.portfolio")
    assert log is not None
    # Smoke: it should accept structured kwargs without raising
    _capture(lambda: log.info("e", a=1, b="x"))
