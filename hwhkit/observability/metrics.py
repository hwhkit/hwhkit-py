"""Shared meter + standard metric registry.

Standard metrics(spec § 4.4)— created lazily on first access so that they
register against whichever ``MeterProvider`` is current at access time:
- ``http.server.request.duration`` (Histogram, ms)
- ``http.server.active_requests`` (UpDownCounter)
- ``db.client.operation.duration`` (Histogram, ms)
- ``redis.command.duration`` (Histogram, ms)
- ``messaging.publish.duration`` (Histogram, ms)
- ``messaging.consume.duration`` (Histogram, ms)
- ``scheduler.job.duration`` (Histogram, ms)
"""

from __future__ import annotations

from typing import Any


def get_meter() -> Any:
    """Return the framework's named OTel meter."""
    from opentelemetry import metrics

    return metrics.get_meter("hwhkit")


class StandardMetrics:
    """Lazy registry of the standard metric set."""

    _instance: StandardMetrics | None = None

    def __init__(self) -> None:
        m = get_meter()
        self.http_request_duration = m.create_histogram(
            "http.server.request.duration",
            unit="ms",
            description="HTTP server request duration",
        )
        self.http_active_requests = m.create_up_down_counter(
            "http.server.active_requests",
            unit="{request}",
            description="In-flight HTTP server requests",
        )
        self.db_operation_duration = m.create_histogram(
            "db.client.operation.duration",
            unit="ms",
            description="DB client operation duration",
        )
        self.redis_command_duration = m.create_histogram(
            "redis.command.duration",
            unit="ms",
            description="Redis command duration",
        )
        self.messaging_publish_duration = m.create_histogram(
            "messaging.publish.duration",
            unit="ms",
            description="Message bus publish duration",
        )
        self.messaging_consume_duration = m.create_histogram(
            "messaging.consume.duration",
            unit="ms",
            description="Message bus consume duration",
        )
        self.scheduler_job_duration = m.create_histogram(
            "scheduler.job.duration",
            unit="ms",
            description="Scheduler job execution duration",
        )


def standard_metrics() -> StandardMetrics:
    """Return cached standard-metrics instance, creating on first call."""
    if StandardMetrics._instance is None:
        StandardMetrics._instance = StandardMetrics()
    return StandardMetrics._instance


def reset_standard_metrics() -> None:
    """Drop the cache; next call to ``standard_metrics()`` re-binds to current MeterProvider."""
    StandardMetrics._instance = None


__all__ = ["StandardMetrics", "get_meter", "reset_standard_metrics", "standard_metrics"]
