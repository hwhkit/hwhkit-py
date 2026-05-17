"""Tests for hwhkit.observability.metrics."""

from __future__ import annotations

from hwhkit.observability.metrics import (
    StandardMetrics,
    get_meter,
    reset_standard_metrics,
    standard_metrics,
)


def test_get_meter_returns_meter() -> None:
    m = get_meter()
    assert m is not None
    # Smoke: create a counter (proves it's a real Meter)
    c = m.create_counter("test.counter")
    c.add(1)


def test_standard_metrics_lazy_singleton() -> None:
    reset_standard_metrics()
    a = standard_metrics()
    b = standard_metrics()
    assert a is b
    assert isinstance(a, StandardMetrics)
    assert a.http_request_duration is not None
    assert a.http_active_requests is not None
    assert a.db_operation_duration is not None
    assert a.redis_command_duration is not None
    assert a.messaging_publish_duration is not None
    assert a.messaging_consume_duration is not None
    assert a.scheduler_job_duration is not None


def test_reset_clears_singleton() -> None:
    reset_standard_metrics()
    a = standard_metrics()
    reset_standard_metrics()
    b = standard_metrics()
    assert a is not b
